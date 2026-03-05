from fastapi import APIRouter

from . import identity
from . import account

__all__ = [
    'router',
]
router = APIRouter()

router.include_router(identity.router)
router.include_router(account.router)
