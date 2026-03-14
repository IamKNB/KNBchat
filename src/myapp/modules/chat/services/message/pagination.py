from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col

from myapp.modules.chat.schemas import Message
from myapp.common.errors import raise_service_error
from myapp.modules.chat.services.pagination import (
    MAX_PAGE_LIMIT,
    decode_cursor_payload,
    encode_cursor_payload,
    validate_limit as validate_page_limit,
)

__all__ = [
    "KeysetAnchor",
    "build_keyset_filter",
    "decode_cursor",
    "encode_cursor",
    "validate_limit",
]


@dataclass
class KeysetAnchor:
    sort_time: datetime
    message_id: UUID


def encode_cursor(anchor: KeysetAnchor) -> str:
    payload = {
        "sort_time": anchor.sort_time.isoformat(),
        "message_id": str(anchor.message_id),
    }
    return encode_cursor_payload(payload)


def decode_cursor(cursor: str | None) -> KeysetAnchor | None:
    payload = decode_cursor_payload(cursor)
    if payload is None:
        return None
    try:
        sort_time = datetime.fromisoformat(payload["sort_time"])
        message_id = UUID(payload["message_id"])
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

    return KeysetAnchor(sort_time=sort_time, message_id=message_id)


def validate_limit(limit: int) -> None:
    validate_page_limit(limit, MAX_PAGE_LIMIT)


def build_keyset_filter(*, anchor: KeysetAnchor) -> ColumnElement[bool]:
    return or_(
        col(Message.created_at) < anchor.sort_time,
        and_(
            col(Message.created_at) == anchor.sort_time,
            col(Message.id) < anchor.message_id,
        ),
    )
