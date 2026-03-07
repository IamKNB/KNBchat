from datetime import datetime, UTC
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index
from sqlmodel import Field, SQLModel, Relationship

__all__ = [
    "BaseFriendship",
    "Friendship",
    "Friendship2Self",
    "FriendshipStatus",
    "FriendshipApplySource",
]
if TYPE_CHECKING:
    from auth.user import User


class FriendshipStatus(str, Enum):
    pending = "pending"  # 申请中，未处理
    accepted = "accepted"  # 已成为好友
    rejected = "rejected"  # 已拒绝


class FriendshipApplySource(str, Enum):
    search = "search"  # 查找
    email = "email"  # 邮箱
    other = "other"


class BaseFriendship(SQLModel):
    # 状态
    status: FriendshipStatus = Field(default=FriendshipStatus.pending)
    # 记录时间
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    accepted_at: datetime | None = Field(default=None)


class Friendship(BaseFriendship, table=True):
    __tablename__ = "friendship"
    __table_args__ = (
        Index(
            "ix_friendship_addressee_status",
            "addressee_id",
            "status",
        ),
    )
    # 申请者
    requester_id: UUID = Field(foreign_key="user.id", primary_key=True)
    # 接受者
    addressee_id: UUID = Field(foreign_key="user.id", primary_key=True)
    # 无向关系唯一键：按 requester/addressee 升序拼接
    pair_key: str = Field(
        min_length=65,
        max_length=65,
        unique=True,
        nullable=False,
    )
    # 申请消息
    request_message: str | None = Field(
        default=None,
        max_length=200,
    )
    # 查找来源
    source: FriendshipApplySource = Field(default=FriendshipApplySource.search)
    # 关系：这条好友记录的发起人
    requester: "User" = Relationship(
        back_populates="sent_friendships",
        sa_relationship_kwargs={
            "foreign_keys": "Friendship.requester_id",
            "lazy": "selectin",
        },
    )

    # 关系：这条好友记录的接收人
    addressee: "User" = Relationship(
        back_populates="received_friendships",
        sa_relationship_kwargs={
            "foreign_keys": "Friendship.addressee_id",
            "lazy": "selectin",
        },
    )

    @staticmethod
    def build_pair_key(requester_id: UUID, addressee_id: UUID) -> str:
        left, right = sorted((requester_id.hex, addressee_id.hex))
        return f"{left}:{right}"


class Friendship2Self(BaseFriendship):
    requester_id: UUID
    addressee_id: UUID
    source: FriendshipApplySource
    request_message: str | None = None
