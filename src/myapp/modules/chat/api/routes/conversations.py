from uuid import UUID

from fastapi import APIRouter, Depends, status

from auth import get_user
from auth.user import User
from db import SessionDep
from myapp.common.api import PaginationParams
from myapp.modules.chat.api.errors.chat import CHAT_ERROR_RESPONSES, ChatRoute
from myapp.modules.chat.schemas.chat_api import (
    ConversationEnvelope,
    ConversationListEnvelope,
    ConversationMemberActionEnvelope,
    CreateDirectConversationBody,
    CreateGroupConversationBody,
    InviteMembersBody,
)
from myapp.modules.chat.services.chat_response import (
    build_conversation_envelope,
    build_conversation_list_envelope,
    build_member_action_envelope,
)
from myapp.modules.chat.services.conversation.service import (
    create_group_conversation,
    create_or_get_direct_conversation,
    invite_group_members,
    leave_group,
    list_conversations,
    remove_group_member,
)

__all__ = ["router"]

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    route_class=ChatRoute,
    responses=CHAT_ERROR_RESPONSES,
)


@router.post("/direct", response_model=ConversationEnvelope, status_code=status.HTTP_201_CREATED)
def create_direct_conversation(
        body: CreateDirectConversationBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ConversationEnvelope:
    bundle = create_or_get_direct_conversation(
        session=session,
        actor=current_user,
        peer_id=body.peer_id,
    )
    return build_conversation_envelope(
        bundle,
        code="conversation_created",
        message="conversation created",
    )


@router.post("", response_model=ConversationEnvelope, status_code=status.HTTP_201_CREATED)
def create_group_conversation_route(
        body: CreateGroupConversationBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ConversationEnvelope:
    bundle = create_group_conversation(
        session=session,
        actor=current_user,
        name=body.name,
        member_ids=body.member_ids,
    )
    return build_conversation_envelope(
        bundle,
        code="conversation_created",
        message="conversation created",
    )


@router.get("", response_model=ConversationListEnvelope)
def list_conversations_route(
        session: SessionDep,
        current_user: User = Depends(get_user),
        pagination: PaginationParams = Depends(),
) -> ConversationListEnvelope:
    page = list_conversations(
        session=session,
        actor=current_user,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )
    return build_conversation_list_envelope(
        page,
        code="conversations_listed",
        message="conversations listed",
    )


@router.post("/{conversation_id}/members", response_model=ConversationMemberActionEnvelope)
def invite_members(
        conversation_id: UUID,
        body: InviteMembersBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ConversationMemberActionEnvelope:
    added = invite_group_members(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
        member_ids=body.member_ids,
    )
    return build_member_action_envelope(
        conversation_id=conversation_id,
        member_ids=added,
        code="conversation_members_added",
        message="conversation members added",
    )


@router.delete("/{conversation_id}/members/me", response_model=ConversationMemberActionEnvelope)
def leave_group_route(
        conversation_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ConversationMemberActionEnvelope:
    removed_id = leave_group(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
    )
    return build_member_action_envelope(
        conversation_id=conversation_id,
        member_ids=[removed_id],
        code="conversation_member_left",
        message="conversation member left",
    )


@router.delete("/{conversation_id}/members/{user_id}", response_model=ConversationMemberActionEnvelope)
def remove_member(
        conversation_id: UUID,
        user_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ConversationMemberActionEnvelope:
    removed_id = remove_group_member(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
        member_id=user_id,
    )
    return build_member_action_envelope(
        conversation_id=conversation_id,
        member_ids=[removed_id],
        code="conversation_member_removed",
        message="conversation member removed",
    )
