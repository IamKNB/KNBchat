from typing import Any
from uuid import UUID

from sqlmodel import Session, col, select

from auth.user import User
from myapp.modules.chat.schemas import Friendship
from myapp.modules.chat.services.pagination import apply_keyset_filter

from .pagination import (
    KeysetAnchor,
    build_keyset_filter,
    decode_cursor,
    encode_cursor,
    sort_time_expr,
    sort_time_of,
    validate_limit,
)
from .types import FriendshipListMode, FriendshipPage

__all__ = [
    "delete_friendship",
    "get_friendship_by_pair_ids",
    "get_friendship_by_user_ids",
    "get_user_by_id",
    "list_friendships_page",
    "normalize_pair_ids",
    "save_friendship",
]


def normalize_pair_ids(user_a_id: UUID, user_b_id: UUID) -> tuple[UUID, UUID]:
    if user_a_id.hex <= user_b_id.hex:
        return user_a_id, user_b_id
    return user_b_id, user_a_id


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def _ensure_friendship_users_loaded(friendship: Friendship) -> Friendship:
    _ = friendship.requester
    _ = friendship.addressee
    return friendship


def get_friendship_by_pair_ids(
        session: Session,
        pair_low_id: UUID,
        pair_high_id: UUID,
) -> Friendship | None:
    friendship = session.exec(
        select(Friendship).where(
            Friendship.pair_low_id == pair_low_id,
            Friendship.pair_high_id == pair_high_id,
        )
    ).first()
    if friendship is None:
        return None
    return _ensure_friendship_users_loaded(friendship)


def get_friendship_by_user_ids(
        session: Session,
        user_a_id: UUID,
        user_b_id: UUID,
) -> Friendship | None:
    pair_low_id, pair_high_id = normalize_pair_ids(user_a_id, user_b_id)
    return get_friendship_by_pair_ids(session, pair_low_id, pair_high_id)


def save_friendship(session: Session, friendship: Friendship) -> Friendship:
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    refreshed = get_friendship_by_pair_ids(session, friendship.pair_low_id, friendship.pair_high_id)
    return refreshed or friendship


def delete_friendship(session: Session, friendship: Friendship) -> Friendship:
    snapshot = _ensure_friendship_users_loaded(friendship)
    session.delete(friendship)
    session.commit()
    return snapshot


def list_friendships_page(
        session: Session,
        *,
        filters: list[Any],
        cursor: str | None,
        limit: int,
        mode: FriendshipListMode,
) -> FriendshipPage:
    validate_limit(limit)
    anchor = decode_cursor(cursor)
    current_sort_expr = sort_time_expr(mode)

    statement = select(Friendship).where(*filters)
    statement = apply_keyset_filter(
        statement,
        anchor,
        build_keyset_filter,
        current_sort_expr=current_sort_expr,
    )

    statement = statement.order_by(
        current_sort_expr.desc(),
        col(Friendship.pair_low_id).desc(),
        col(Friendship.pair_high_id).desc(),
    ).limit(limit + 1)

    rows = list(session.exec(statement))
    has_more = len(rows) > limit
    items = [_ensure_friendship_users_loaded(item) for item in rows[:limit]]

    next_cursor: str | None = None
    if has_more and items:
        last = items[-1]
        next_anchor = KeysetAnchor(
            sort_time=sort_time_of(last, mode),
            pair_low_id=last.pair_low_id,
            pair_high_id=last.pair_high_id,
        )
        next_cursor = encode_cursor(next_anchor)

    return FriendshipPage(
        items=items,
        has_more=has_more,
        next_cursor=next_cursor,
    )
