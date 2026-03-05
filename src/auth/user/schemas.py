import uuid
from datetime import datetime, UTC, timedelta
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from db.through import UserPermissionGroupLink

if TYPE_CHECKING:
    from auth.permissions import PermissionGroup

__all__ = [
    "BaseUser",
    "User",
    "CreateUser",
    "User2Public",
    "User2Friends",
    "User2Self",
]


# 最最基本信息，未登陆的匿名者都可以请求的基本信息，要求不能包含任何泄漏价值的信息
class BaseUser(SQLModel):
    username: str | None = Field(index=True, default=None)
    avatar_url: str | None = Field(default=None)  # todo:实现URL存储


# 数据库存储的最全面信息，包含上面的信息
class User(BaseUser, table=True):
    # 账号信息
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    # 个人信息
    age: int | None = None
    email: str = Field(index=True, unique=True)
    password: str

    # 权限与群组
    permission_groups: list["PermissionGroup"] = Relationship(back_populates="users",
                                                              link_model=UserPermissionGroupLink)
    # 风控信息
    is_active: bool = True
    access_token_expires_timedelta: timedelta = Field(default=timedelta(minutes=30))
    refresh_token_expires_timedelta: timedelta = Field(default=timedelta(days=31))


# 创建用户
class CreateUser(BaseUser):
    email: str
    password: str


# 从下面开始不同安全级别可见信息
# 登陆的陌生用户可见信息
class User2Public(BaseUser):
    id: uuid.UUID


# 对于好友可见的信息
class User2Friends(BaseUser):
    id: uuid.UUID = Field(index=True)
    email: str

    age: int | None

    is_active: bool

    created_at: datetime


# 自我可见信息
class User2Self(BaseUser):
    id: uuid.UUID = Field(index=True)
    email: str
    age: int | None = None
    is_active: bool
    created_at: datetime


# 定义用户的好友关系
class UsersLink(SQLModel):
    pass
