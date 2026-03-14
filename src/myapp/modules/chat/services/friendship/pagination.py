from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from typing import Any, cast

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col, func

from myapp.common.errors import raise_service_error
from myapp.modules.chat.schemas import Friendship
from myapp.modules.chat.services.pagination import (
    MAX_PAGE_LIMIT,
    decode_cursor_payload,
    encode_cursor_payload,
    validate_limit as validate_page_limit,
)
from .types import FriendshipListMode

__all__ = [
    "KeysetAnchor",
    "build_keyset_filter",
    "decode_cursor",
    "encode_cursor",
    "sort_time_expr",
    "sort_time_of",
    "validate_limit",
]


@dataclass
class KeysetAnchor:
    sort_time: datetime
    pair_low_id: UUID
    pair_high_id: UUID


def encode_cursor(anchor: KeysetAnchor) -> str:
    payload = {
        "sort_time": anchor.sort_time.isoformat(),
        "pair_low_id": str(anchor.pair_low_id),
        "pair_high_id": str(anchor.pair_high_id),
    }
    return encode_cursor_payload(payload)


def decode_cursor(cursor: str | None) -> KeysetAnchor | None:
    payload = decode_cursor_payload(cursor)
    if payload is None:
        return None
    try:
        sort_time = datetime.fromisoformat(payload["sort_time"])
        pair_low_id = UUID(payload["pair_low_id"])
        pair_high_id = UUID(payload["pair_high_id"])
    except (
            ValueError,
            TypeError,
            KeyError,
    ):
        raise_service_error(
            status_code=400,
            code="invalid_cursor",
            message="invalid cursor",
            detail=cursor,
        )

    return KeysetAnchor(
        sort_time=sort_time,
        pair_low_id=pair_low_id,
        pair_high_id=pair_high_id,
    )


def validate_limit(limit: int) -> None:
    validate_page_limit(limit, MAX_PAGE_LIMIT)


def sort_time_expr(mode: FriendshipListMode) -> ColumnElement[Any]:
    if mode == FriendshipListMode.accepted:
        return cast(
            ColumnElement[Any],
            func.coalesce(
                col(Friendship.accepted_at),
                col(Friendship.created_at),
            ),
        )
    return cast(
        ColumnElement[Any],
        cast(object, col(Friendship.created_at)),
    )


def sort_time_of(item: Friendship, mode: FriendshipListMode) -> datetime:
    if mode == FriendshipListMode.accepted:
        return item.accepted_at or item.created_at
    return item.created_at


def build_keyset_filter(
        *,
        current_sort_expr: ColumnElement[Any],
        anchor: KeysetAnchor,
) -> ColumnElement[bool]:
    return or_(
        current_sort_expr < anchor.sort_time,
        and_(
            current_sort_expr == anchor.sort_time,
            col(Friendship.pair_low_id) < anchor.pair_low_id,
        ),
        and_(
            current_sort_expr == anchor.sort_time,
            col(Friendship.pair_low_id) == anchor.pair_low_id,
            col(Friendship.pair_high_id) < anchor.pair_high_id,
        ),
    )
