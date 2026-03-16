from auth.user import User2Public
from myapp.common.api import ListEnvelope

__all__ = [
    "UserPublicListEnvelope",
]

UserPublicListEnvelope = ListEnvelope[User2Public]
