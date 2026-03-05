from sqlmodel import SQLModel, Field, Relationship

from auth.permissions import PermissionGroup
from db.through import PermissionGroupScopesLink

__all__ = ["Scope", ]


class Scope(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str
    description: str

    permission_groups: list[PermissionGroup] = Relationship(back_populates="scopes",
                                                            link_model=PermissionGroupScopesLink)
