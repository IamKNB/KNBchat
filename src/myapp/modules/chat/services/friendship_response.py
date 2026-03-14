from uuid import UUID

from auth.user import User2Friends, User2Public
from myapp.common.api import CursorMeta
from myapp.modules.chat.schemas import Friendship
from myapp.modules.chat.schemas.friendship_api import (
    FriendshipAcceptedData,
    FriendshipAcceptedEnvelope,
    FriendshipAcceptedListEnvelope,
    FriendshipDirection,
    FriendshipPendingData,
    FriendshipPendingEnvelope,
    FriendshipPendingListEnvelope,
)
from .friendship import FriendshipPage

__all__ = [
    "build_accept_friendship_response",
    "build_cancel_friendship_response",
    "build_create_friendship_response",
    "build_list_accepted_friendships_response",
    "build_list_friendship_requests_response",
    "build_reject_friendship_response",
    "build_remove_friendship_response",
]


def _direction_of(friendship: Friendship, actor_id: UUID) -> FriendshipDirection:
    if friendship.requester_id == actor_id:
        return FriendshipDirection.outgoing
    return FriendshipDirection.incoming


def _pending_peer(friendship: Friendship, actor_id: UUID) -> User2Public:
    if friendship.requester_id == actor_id:
        return User2Public.model_validate(friendship.addressee)
    return User2Public.model_validate(friendship.requester)


def _accepted_peer(friendship: Friendship, actor_id: UUID) -> User2Friends:
    if friendship.requester_id == actor_id:
        return User2Friends.model_validate(friendship.addressee)
    return User2Friends.model_validate(friendship.requester)


def _to_pending_data(friendship: Friendship, actor_id: UUID) -> FriendshipPendingData:
    return FriendshipPendingData(
        status=friendship.status,
        created_at=friendship.created_at,
        source=friendship.source,
        request_message=friendship.request_message,
        peer=_pending_peer(friendship, actor_id),
        direction=_direction_of(friendship, actor_id),
    )


def _to_accepted_data(friendship: Friendship, actor_id: UUID) -> FriendshipAcceptedData:
    return FriendshipAcceptedData(
        status=friendship.status,
        created_at=friendship.created_at,
        accepted_at=friendship.accepted_at,
        source=friendship.source,
        request_message=friendship.request_message,
        peer=_accepted_peer(friendship, actor_id),
        direction=_direction_of(friendship, actor_id),
    )


def build_create_friendship_response(
        friendship: Friendship,
        actor_id: UUID,
) -> FriendshipPendingEnvelope:
    return FriendshipPendingEnvelope(
        code="friendship_request_created",
        message="friendship request created",
        data=_to_pending_data(friendship, actor_id),
    )


def build_accept_friendship_response(
        friendship: Friendship,
        actor_id: UUID,
) -> FriendshipAcceptedEnvelope:
    return FriendshipAcceptedEnvelope(
        code="friendship_request_accepted",
        message="friendship request accepted",
        data=_to_accepted_data(friendship, actor_id),
    )


def build_reject_friendship_response(
        friendship: Friendship,
        actor_id: UUID,
) -> FriendshipPendingEnvelope:
    return FriendshipPendingEnvelope(
        code="friendship_request_rejected",
        message="friendship request rejected",
        data=_to_pending_data(friendship, actor_id),
    )


def build_cancel_friendship_response(
        friendship: Friendship,
        actor_id: UUID,
) -> FriendshipPendingEnvelope:
    return FriendshipPendingEnvelope(
        code="friendship_request_canceled",
        message="friendship request canceled",
        data=_to_pending_data(friendship, actor_id),
    )


def build_remove_friendship_response(
        friendship: Friendship,
        actor_id: UUID,
) -> FriendshipAcceptedEnvelope:
    return FriendshipAcceptedEnvelope(
        code="friendship_removed",
        message="friendship removed",
        data=_to_accepted_data(friendship, actor_id),
    )


def build_list_friendship_requests_response(
        page: FriendshipPage,
        actor_id: UUID,
) -> FriendshipPendingListEnvelope:
    return FriendshipPendingListEnvelope(
        code="friendship_requests_listed",
        message="friendship requests listed",
        data=[_to_pending_data(item, actor_id) for item in page.items],
        meta=CursorMeta(
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        ),
    )


def build_list_accepted_friendships_response(
        page: FriendshipPage,
        actor_id: UUID,
) -> FriendshipAcceptedListEnvelope:
    return FriendshipAcceptedListEnvelope(
        code="friendships_listed",
        message="friendships listed",
        data=[_to_accepted_data(item, actor_id) for item in page.items],
        meta=CursorMeta(
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        ),
    )
