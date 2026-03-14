from dataclasses import dataclass
from enum import Enum

from myapp.modules.chat.schemas import Friendship
from myapp.modules.chat.services.pagination import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

__all__ = [
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
    "FriendshipListMode",
    "FriendshipPage",
]


class FriendshipListMode(str, Enum):
    pending = "pending"
    accepted = "accepted"


@dataclass
class FriendshipPage:
    items: list[Friendship]
    has_more: bool
    next_cursor: str | None
