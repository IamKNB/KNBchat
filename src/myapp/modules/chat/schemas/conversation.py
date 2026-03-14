from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, Index, SQLModel, UniqueConstraint

__all__ = [
    "Conversation",
    "ConversationMember",
    "ConversationMemberRole",
    "ConversationType",
]


class ConversationType(str, Enum):
    direct = "direct"
    group = "group"


class ConversationMemberRole(str, Enum):
    owner = "owner"
    member = "member"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"
    __table_args__ = (
        UniqueConstraint(
            "type",
            "pair_low_id",
            "pair_high_id",
            name="uq_conversation_direct_pair",
        ),
        Index("ix_conversation_type_created_at", "type", "created_at"),
        Index("ix_conversation_created_by", "created_by"),
        Index("ix_conversation_pair_low", "pair_low_id"),
        Index("ix_conversation_pair_high", "pair_high_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: ConversationType = Field(nullable=False)
    name: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    created_by: UUID = Field(foreign_key="user.id", nullable=False)
    pair_low_id: UUID | None = Field(foreign_key="user.id", default=None, nullable=True)
    pair_high_id: UUID | None = Field(foreign_key="user.id", default=None, nullable=True)


class ConversationMember(SQLModel, table=True):
    __tablename__ = "conversation_member"
    __table_args__ = (
        Index("ix_conversation_member_user", "user_id"),
        Index("ix_conversation_member_conversation", "conversation_id"),
    )

    conversation_id: UUID = Field(foreign_key="conversation.id", primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    role: ConversationMemberRole = Field(default=ConversationMemberRole.member, nullable=False)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
