from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, SQLModel, Relationship

__all__ = [
    "BaseUserBlock",
    "UserBlock",
]
if TYPE_CHECKING:
    from auth.user import User


class BaseUserBlock(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    reason: str | None = Field(default=None)


class UserBlock(BaseUserBlock, table=True):
    __tablename__ = "user_block"

    blocker_id: UUID = Field(foreign_key="user.id", primary_key=True)
    blocked_id: UUID = Field(foreign_key="user.id", primary_key=True, index=True)

    blocker: "User" = Relationship(
        back_populates="sent_blocks",
        sa_relationship_kwargs={
            "foreign_keys": "UserBlock.blocker_id",
            "lazy": "selectin",
        },
    )
    blocked: "User" = Relationship(
        back_populates="received_blocks",
        sa_relationship_kwargs={
            "foreign_keys": "UserBlock.blocked_id",
            "lazy": "selectin",
        },
    )
