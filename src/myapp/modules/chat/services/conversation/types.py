from dataclasses import dataclass

from auth.user import User
from myapp.modules.chat.schemas import Conversation
from myapp.modules.chat.services.pagination import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

__all__ = [
    "ConversationBundle",
    "ConversationPage",
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
]


@dataclass
class ConversationBundle:
    conversation: Conversation
    peer: User | None


@dataclass
class ConversationPage:
    items: list[ConversationBundle]
    has_more: bool
    next_cursor: str | None
