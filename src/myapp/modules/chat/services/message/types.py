from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from auth.user import User
from myapp.modules.chat.schemas import Message
from myapp.modules.chat.services.pagination import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

__all__ = [
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
    "MessagePage",
    "MessageReadView",
]


@dataclass
class MessagePage:
    items: list[Message]
    has_more: bool
    next_cursor: str | None


@dataclass
class MessageReadView:
    message_id: UUID
    reader: User
    read_at: datetime
