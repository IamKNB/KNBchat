from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlmodel import SQLModel

from auth.user import User2Friends, User2Public
from myapp.common.api import Envelope, ListEnvelope
from .friendship import FriendshipApplySource, FriendshipStatus

__all__ = [
    "CreateFriendshipRequestBody",
    "FriendshipAcceptedData",
    "FriendshipAcceptedEnvelope",
    "FriendshipAcceptedListEnvelope",
    "FriendshipDirection",
    "FriendshipPendingData",
    "FriendshipPendingEnvelope",
    "FriendshipPendingListEnvelope",
]

class FriendshipDirection(str, Enum):
    incoming = "incoming"
    outgoing = "outgoing"


class CreateFriendshipRequestBody(SQLModel):
    addressee_id: UUID
    request_message: str | None = None
    source: FriendshipApplySource = FriendshipApplySource.search


class FriendshipPendingData(SQLModel):
    status: FriendshipStatus
    created_at: datetime
    source: FriendshipApplySource
    request_message: str | None = None
    peer: User2Public
    direction: FriendshipDirection


class FriendshipAcceptedData(SQLModel):
    status: FriendshipStatus
    created_at: datetime
    accepted_at: datetime | None
    source: FriendshipApplySource
    request_message: str | None = None
    peer: User2Friends
    direction: FriendshipDirection


FriendshipPendingEnvelope = Envelope[FriendshipPendingData]
FriendshipAcceptedEnvelope = Envelope[FriendshipAcceptedData]
FriendshipPendingListEnvelope = ListEnvelope[FriendshipPendingData]
FriendshipAcceptedListEnvelope = ListEnvelope[FriendshipAcceptedData]
