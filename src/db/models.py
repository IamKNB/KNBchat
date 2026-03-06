"""Model imports to populate SQLModel metadata before create_all."""

from auth.permissions import PermissionGroup, Scope
from auth.user import User
from db.through import PermissionGroupScopesLink, UserPermissionGroupLink
from myapp.modules.chat import Friendship

__all__ = [
    "User",
    "PermissionGroup",
    "Scope",
    "UserPermissionGroupLink",
    "PermissionGroupScopesLink",
    "Friendship",
]
