from fastapi import APIRouter

from . import conversations
from . import friendship
from . import messages

__all__ = ["router"]

router = APIRouter()
router.include_router(conversations.router)
router.include_router(friendship.router)
router.include_router(messages.router)
