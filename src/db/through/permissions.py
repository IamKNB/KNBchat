from datetime import datetime, UTC
from uuid import UUID

from sqlmodel import SQLModel, Field

__all__ = [
    "UserPermissionGroupLink",
    "PermissionGroupScopesLink",
]


class UserPermissionGroupLink(SQLModel, table=True):
    __tablename__ = "user_link_permission_group"
    user_id: UUID = Field(primary_key=True, foreign_key="user.id")
    permission_group_id: int | None = Field(primary_key=True, default=None, foreign_key="permission_group.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class PermissionGroupScopesLink(SQLModel, table=True):
    __tablename__ = "permission_group_link_scopes"
    permission_group_id: int | None = Field(primary_key=True, default=None, foreign_key="permission_group.id")
    scope_id: int | None = Field(primary_key=True, default=None, foreign_key="scope.id")
