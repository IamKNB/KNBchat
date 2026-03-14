from uuid import UUID

from sqlmodel import Session, select

from auth.user import User
from myapp.common.errors import raise_service_error
from myapp.modules.chat.schemas import (
    Conversation,
    ConversationMember,
    ConversationMemberRole,
    FriendshipStatus,
    Message,
)
from myapp.modules.chat.services.block import is_blocked_by_ids
from myapp.modules.chat.services.friendship.repo import get_friendship_by_user_ids

__all__ = [
    "require_conversation",
    "require_member",
    "require_owner",
    "require_user_exists",
    "require_friendship_accepted",
    "require_not_blocked",
    "require_message",
    "list_other_members",
]


def require_user_exists(session: Session, user_id: UUID) -> User:
    user: User | None = session.get(User, user_id)
    if user is None:
        raise_service_error(
            status_code=404,
            code="user_not_found",
            message="user not found",
            detail=str(user_id),
        )
    return user


def require_friendship_accepted(session: Session, user_a_id: UUID, user_b_id: UUID) -> None:
    friendship = get_friendship_by_user_ids(session, user_a_id, user_b_id)
    if friendship is None or friendship.status != FriendshipStatus.accepted:
        raise_service_error(
            status_code=403,
            code="friendship_required",
            message="friendship required",
            detail="friendship must be accepted before chatting",
        )


def require_not_blocked(session: Session, user_a_id: UUID, user_b_id: UUID) -> None:
    if is_blocked_by_ids(session, user_a_id, user_b_id):
        raise_service_error(
            status_code=409,
            code="user_blocked",
            message="user blocked",
            detail="chat is blocked between these users",
        )


def require_conversation(session: Session, conversation_id: UUID) -> Conversation:
    conversation: Conversation | None = session.get(Conversation, conversation_id)
    if conversation is None:
        raise_service_error(
            status_code=404,
            code="conversation_not_found",
            message="conversation not found",
            detail=str(conversation_id),
        )
    return conversation


def require_member(session: Session, *, conversation_id: UUID, user_id: UUID) -> ConversationMember:
    member: ConversationMember | None = session.get(ConversationMember, (conversation_id, user_id))
    if member is None:
        raise_service_error(
            status_code=403,
            code="conversation_forbidden",
            message="forbidden conversation operation",
            detail="user is not a conversation member",
        )
    return member


def require_owner(session: Session, *, conversation_id: UUID, user_id: UUID) -> ConversationMember:
    member = require_member(session, conversation_id=conversation_id, user_id=user_id)
    if member.role != ConversationMemberRole.owner:
        raise_service_error(
            status_code=403,
            code="conversation_forbidden",
            message="forbidden conversation operation",
            detail="only owner can manage members",
        )
    return member


def require_message(session: Session, message_id: UUID) -> Message:
    message: Message | None = session.get(Message, message_id)
    if message is None:
        raise_service_error(
            status_code=404,
            code="message_not_found",
            message="message not found",
            detail=str(message_id),
        )
    return message


def list_other_members(session: Session, *, conversation_id: UUID, user_id: UUID) -> list[ConversationMember]:
    return list(
        session.exec(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id != user_id,
            ),
        )
    )
