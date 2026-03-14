from uuid import UUID

from sqlmodel import Session, select

from myapp.modules.chat.schemas import Conversation, ConversationMember, ConversationType

__all__ = [
    "get_conversation",
    "get_direct_conversation_by_pair",
    "get_member",
    "list_members",
    "list_members_excluding_user",
]


def get_conversation(session: Session, conversation_id: UUID) -> Conversation | None:
    return session.get(Conversation, conversation_id)


def get_direct_conversation_by_pair(
        session: Session,
        *,
        pair_low_id: UUID,
        pair_high_id: UUID,
) -> Conversation | None:
    return session.exec(
        select(Conversation).where(
            Conversation.type == ConversationType.direct,
            Conversation.pair_low_id == pair_low_id,
            Conversation.pair_high_id == pair_high_id,
        )
    ).first()


def list_members(session: Session, conversation_id: UUID) -> list[ConversationMember]:
    return list(
        session.exec(
            select(ConversationMember).where(ConversationMember.conversation_id == conversation_id),
        )
    )


def list_members_excluding_user(
        session: Session,
        *,
        conversation_id: UUID,
        user_id: UUID,
) -> list[ConversationMember]:
    return list(
        session.exec(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id != user_id,
            ),
        )
    )


def get_member(session: Session, conversation_id: UUID, user_id: UUID) -> ConversationMember | None:
    return session.get(ConversationMember, (conversation_id, user_id))
