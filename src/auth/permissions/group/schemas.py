from typing import TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from db.through import PermissionGroupScopesLink, UserPermissionGroupLink

if TYPE_CHECKING:
    from auth.permissions import Scope
    from auth.user import User

__all__ = ["PermissionGroup", ]


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_group"
    id: int | None = Field(default=None, primary_key=True)

    users: list["User"] = Relationship(back_populates="permission_groups", link_model=UserPermissionGroupLink)
    scopes: list["Scope"] = Relationship(back_populates="permission_groups", link_model=PermissionGroupScopesLink)
