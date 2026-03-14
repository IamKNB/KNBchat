from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from auth import get_user
from auth.user import User
from db import SessionDep
from myapp.common.api import PaginationParams
from myapp.modules.chat.api.errors.friendship import FRIENDSHIP_ERROR_RESPONSES, FriendshipRoute
from myapp.modules.chat.schemas.friendship_api import (
    CreateFriendshipRequestBody,
    FriendshipAcceptedEnvelope,
    FriendshipAcceptedListEnvelope,
    FriendshipDirection,
    FriendshipPendingEnvelope,
    FriendshipPendingListEnvelope,
)
from myapp.modules.chat.services.friendship.service import (
    accept_friendship_request,
    cancel_friendship_request,
    create_friendship_request,
    list_accepted_friendships,
    list_friendship_requests,
    reject_friendship_request,
    remove_friendship,
)
from myapp.modules.chat.services.friendship_response import (
    build_accept_friendship_response,
    build_cancel_friendship_response,
    build_create_friendship_response,
    build_list_accepted_friendships_response,
    build_list_friendship_requests_response,
    build_reject_friendship_response,
    build_remove_friendship_response,
)

__all__ = ["router"]

router = APIRouter(
    prefix="/friendships",
    tags=["friendships"],
    route_class=FriendshipRoute,
    responses=FRIENDSHIP_ERROR_RESPONSES,
)


@router.post("/requests", response_model=FriendshipPendingEnvelope, status_code=status.HTTP_201_CREATED)
def create_friendship(
        body: CreateFriendshipRequestBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> FriendshipPendingEnvelope:
    friendship = create_friendship_request(
        session=session,
        actor=current_user,
        addressee_id=body.addressee_id,
        request_message=body.request_message,
        source=body.source,
    )
    return build_create_friendship_response(friendship, current_user.id)


@router.get("/requests", response_model=FriendshipPendingListEnvelope)
def list_friendship_requests_route(
        session: SessionDep,
        current_user: User = Depends(get_user),
        direction: FriendshipDirection = Query(
            default=FriendshipDirection.incoming,
            description="Request direction. Allowed: incoming, outgoing.",
        ),
        pagination: PaginationParams = Depends(),
) -> FriendshipPendingListEnvelope:
    page = list_friendship_requests(
        session=session,
        actor=current_user,
        direction=direction,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )
    return build_list_friendship_requests_response(
        page,
        current_user.id,
    )


@router.post("/requests/{user_id}/accept", response_model=FriendshipAcceptedEnvelope)
def accept_friendship(
        user_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> FriendshipAcceptedEnvelope:
    friendship = accept_friendship_request(
        session=session,
        actor=current_user,
        requester_id=user_id,
    )
    return build_accept_friendship_response(friendship, current_user.id)


@router.post("/requests/{user_id}/reject", response_model=FriendshipPendingEnvelope)
def reject_friendship(
        user_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> FriendshipPendingEnvelope:
    friendship = reject_friendship_request(
        session=session,
        actor=current_user,
        requester_id=user_id,
    )
    return build_reject_friendship_response(friendship, current_user.id)


@router.delete("/requests/{user_id}", response_model=FriendshipPendingEnvelope)
def cancel_friendship(
        user_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> FriendshipPendingEnvelope:
    friendship = cancel_friendship_request(
        session=session,
        actor=current_user,
        addressee_id=user_id,
    )
    return build_cancel_friendship_response(friendship, current_user.id)


@router.get("", response_model=FriendshipAcceptedListEnvelope)
def list_accepted_friendships_route(
        session: SessionDep,
        current_user: User = Depends(get_user),
        pagination: PaginationParams = Depends(),
) -> FriendshipAcceptedListEnvelope:
    page = list_accepted_friendships(
        session=session,
        actor=current_user,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )
    return build_list_accepted_friendships_response(
        page,
        current_user.id,
    )


@router.delete("/{user_id}", response_model=FriendshipAcceptedEnvelope)
def remove_friendship_route(
        user_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> FriendshipAcceptedEnvelope:
    friendship = remove_friendship(
        session=session,
        actor=current_user,
        friend_user_id=user_id,
    )
    return build_remove_friendship_response(friendship, current_user.id)
