from datetime import UTC, datetime
from typing import NoReturn
from uuid import UUID

from sqlmodel import Session

from auth.user import User
from myapp.common.errors import raise_service_error
from myapp.modules.chat.schemas import Friendship, FriendshipApplySource, FriendshipStatus
from myapp.modules.chat.schemas.friendship_api import FriendshipDirection
from myapp.modules.chat.services.block import is_blocked_by_ids

from .repo import (
    delete_friendship,
    get_friendship_by_pair_ids,
    get_friendship_by_user_ids,
    get_user_by_id,
    list_friendships_page,
    normalize_pair_ids,
    save_friendship,
)
from .types import DEFAULT_PAGE_LIMIT, FriendshipListMode, FriendshipPage

__all__ = [
    "accept_friendship_request",
    "cancel_friendship_request",
    "create_friendship_request",
    "list_accepted_friendships",
    "list_friendship_requests",
    "reject_friendship_request",
    "remove_friendship",
]

REQUEST_MESSAGE_MAX_LENGTH = 200


def _raise_not_found() -> NoReturn:
    raise_service_error(
        status_code=404,
        code="friendship_not_found",
        message="friendship not found",
    )


def _validate_distinct_user_ids(user_a_id: UUID, user_b_id: UUID) -> None:
    if user_a_id == user_b_id:
        raise_service_error(
            status_code=400,
            code="friendship_bad_request",
            message="invalid friendship request",
            detail="friendship users must be different",
        )


def _validate_request_message(request_message: str | None) -> None:
    if request_message is not None and len(request_message) > REQUEST_MESSAGE_MAX_LENGTH:
        raise_service_error(
            status_code=400,
            code="request_message_too_long",
            message="invalid friendship request",
            detail=f"request_message must be at most {REQUEST_MESSAGE_MAX_LENGTH} characters",
        )


def _require_target_user_exists(session: Session, target_user_id: UUID) -> None:
    if get_user_by_id(session, target_user_id) is None:
        _raise_not_found()


def _require_directional_friendship(
        session: Session,
        *,
        requester_id: UUID,
        addressee_id: UUID,
) -> Friendship:
    _validate_distinct_user_ids(requester_id, addressee_id)
    friendship = get_friendship_by_user_ids(session, requester_id, addressee_id)
    if friendship is None:
        _raise_not_found()
    if friendship.requester_id != requester_id or friendship.addressee_id != addressee_id:
        raise_service_error(
            status_code=403,
            code="friendship_forbidden",
            message="forbidden friendship operation",
            detail="requester and addressee do not match friendship direction",
        )
    return friendship


def _require_pending_directional_friendship(
        session: Session,
        *,
        requester_id: UUID,
        addressee_id: UUID,
) -> Friendship:
    friendship = _require_directional_friendship(
        session,
        requester_id=requester_id,
        addressee_id=addressee_id,
    )
    if friendship.status != FriendshipStatus.pending:
        raise_service_error(
            status_code=409,
            code="friendship_state_conflict",
            message="friendship state conflict",
            detail="only pending friendship request can be processed",
        )
    return friendship


def _set_pending_directional_status(
        session: Session,
        *,
        requester_id: UUID,
        addressee_id: UUID,
        target_status: FriendshipStatus,
) -> Friendship:
    friendship = _require_pending_directional_friendship(
        session,
        requester_id=requester_id,
        addressee_id=addressee_id,
    )
    friendship.status = target_status
    friendship.accepted_at = datetime.now(UTC) if target_status == FriendshipStatus.accepted else None
    return save_friendship(session, friendship)


def create_friendship_request(
        session: Session,
        *,
        actor: User,
        addressee_id: UUID,
        request_message: str | None = None,
        source: FriendshipApplySource = FriendshipApplySource.search,
) -> Friendship:
    actor_id = actor.id
    _validate_distinct_user_ids(actor_id, addressee_id)
    _validate_request_message(request_message)
    _require_target_user_exists(session, addressee_id)

    if is_blocked_by_ids(session, actor_id, addressee_id):
        raise_service_error(
            status_code=409,
            code="friendship_blocked",
            message="friendship request blocked",
            detail="friendship request is blocked between these users",
        )

    pair_low_id, pair_high_id = normalize_pair_ids(actor_id, addressee_id)
    if get_friendship_by_pair_ids(session, pair_low_id, pair_high_id) is not None:
        raise_service_error(
            status_code=409,
            code="friendship_conflict",
            message="friendship conflict",
            detail="friendship already exists for this user pair",
        )

    friendship = Friendship(
        requester_id=actor_id,
        addressee_id=addressee_id,
        pair_low_id=pair_low_id,
        pair_high_id=pair_high_id,
        request_message=request_message,
        source=source,
    )
    return save_friendship(session, friendship)


def accept_friendship_request(
        session: Session,
        *,
        actor: User,
        requester_id: UUID,
) -> Friendship:
    return _set_pending_directional_status(
        session,
        requester_id=requester_id,
        addressee_id=actor.id,
        target_status=FriendshipStatus.accepted,
    )


def reject_friendship_request(
        session: Session,
        *,
        actor: User,
        requester_id: UUID,
) -> Friendship:
    return _set_pending_directional_status(
        session,
        requester_id=requester_id,
        addressee_id=actor.id,
        target_status=FriendshipStatus.rejected,
    )


def cancel_friendship_request(
        session: Session,
        *,
        actor: User,
        addressee_id: UUID,
) -> Friendship:
    friendship = _require_pending_directional_friendship(
        session,
        requester_id=actor.id,
        addressee_id=addressee_id,
    )
    return delete_friendship(session, friendship)


def remove_friendship(
        session: Session,
        *,
        actor: User,
        friend_user_id: UUID,
) -> Friendship:
    _validate_distinct_user_ids(actor.id, friend_user_id)
    friendship = get_friendship_by_user_ids(session, actor.id, friend_user_id)
    if friendship is None:
        _raise_not_found()
    if friendship.status != FriendshipStatus.accepted:
        raise_service_error(
            status_code=409,
            code="friendship_state_conflict",
            message="friendship state conflict",
            detail="only accepted friendship can be removed",
        )
    return delete_friendship(session, friendship)


def list_friendship_requests(
        session: Session,
        *,
        actor: User,
        direction: FriendshipDirection = FriendshipDirection.incoming,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
) -> FriendshipPage:
    if direction == FriendshipDirection.incoming:
        filters = [
            Friendship.addressee_id == actor.id,
            Friendship.status == FriendshipStatus.pending,
        ]
    else:
        filters = [
            Friendship.requester_id == actor.id,
            Friendship.status == FriendshipStatus.pending,
        ]
    return list_friendships_page(
        session,
        filters=filters,
        cursor=cursor,
        limit=limit,
        mode=FriendshipListMode.pending,
    )


def list_accepted_friendships(
        session: Session,
        *,
        actor: User,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
) -> FriendshipPage:
    filters = [
        Friendship.status == FriendshipStatus.accepted,
        (Friendship.requester_id == actor.id) | (Friendship.addressee_id == actor.id),
    ]
    return list_friendships_page(
        session,
        filters=filters,
        cursor=cursor,
        limit=limit,
        mode=FriendshipListMode.accepted,
    )
