from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from auth.user import User
from myapp.modules.chat.schemas import Friendship, FriendshipApplySource
from .block import is_blocked

__all__ = [
    "FriendshipValidationError",
    "FriendshipConflictError",
    "create_friendship_request",
]


class FriendshipValidationError(ValueError):
    """Raised when friendship request inputs are invalid."""


class FriendshipConflictError(ValueError):
    """Raised when a friendship for the same user pair already exists."""


def create_friendship_request(
        session: Session,
        requester: User,
        addressee: User,
        *,
        request_message: str | None = None,
        source: FriendshipApplySource = FriendshipApplySource.search,
) -> Friendship:
    if requester.id == addressee.id:
        raise FriendshipValidationError("requester and addressee must be different")

    if request_message is not None and len(request_message) > 200:
        raise FriendshipValidationError("request_message must be at most 200 characters")

    if is_blocked(session, requester, addressee):
        raise FriendshipValidationError("friendship request is blocked between these users")

    pair_key = Friendship.build_pair_key(requester.id, addressee.id)
    existing_pair_key = session.exec(
        select(Friendship.pair_key).where(Friendship.pair_key == pair_key)
    ).first()
    if existing_pair_key is not None:
        raise FriendshipConflictError("friendship already exists for this user pair")

    friendship = Friendship(
        requester_id=requester.id,
        addressee_id=addressee.id,
        pair_key=pair_key,
        request_message=request_message,
        source=source,
    )

    session.add(friendship)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        if "UNIQUE constraint failed: friendship.pair_key" in str(exc.orig):
            raise FriendshipConflictError("friendship already exists for this user pair") from exc
        raise

    session.refresh(friendship)
    return friendship
