from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Index, SQLModel

__all__ = [
    "Message",
    "MessageRead",
]


class Message(SQLModel, table=True):
    __tablename__ = "message"
    __table_args__ = (
        Index("ix_message_conversation_created", "conversation_id", "created_at", "id"),
        Index("ix_message_sender", "sender_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", nullable=False)
    sender_id: UUID = Field(foreign_key="user.id", nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class MessageRead(SQLModel, table=True):
    __tablename__ = "message_read"
    __table_args__ = (
        Index("ix_message_read_message", "message_id"),
        Index("ix_message_read_reader", "reader_id"),
    )

    message_id: UUID = Field(foreign_key="message.id", primary_key=True)
    reader_id: UUID = Field(foreign_key="user.id", primary_key=True)
    read_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
