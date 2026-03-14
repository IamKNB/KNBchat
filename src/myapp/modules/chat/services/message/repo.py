from uuid import UUID

from sqlmodel import Session, select

from myapp.modules.chat.schemas import Message, MessageRead

__all__ = [
    "get_message",
    "list_message_reads",
]


def get_message(session: Session, message_id: UUID) -> Message | None:
    return session.get(Message, message_id)


def list_message_reads(session: Session, message_id: UUID) -> list[MessageRead]:
    return list(
        session.exec(
            select(MessageRead).where(MessageRead.message_id == message_id),
        )
    )
