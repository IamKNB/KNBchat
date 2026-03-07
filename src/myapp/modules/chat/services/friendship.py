from datetime import UTC, datetime

from auth.user import User
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, desc, select

from myapp.modules.chat.schemas import Friendship, FriendshipApplySource, FriendshipStatus
from .block import is_blocked

__all__ = [
    "FriendshipValidationError",
    "FriendshipConflictError",
    "FriendshipNotFoundError",
    "FriendshipPermissionError",
    "FriendshipStateError",
    "get_friendship_between",
    "create_friendship_request",
    "accept_friendship_request",
    "reject_friendship_request",
    "cancel_friendship_request",
    "unfriend",
    "list_incoming_pending_requests",
    "list_outgoing_pending_requests",
    "list_accepted_friendships",
]


class FriendshipValidationError(ValueError):
    """Raised when friendship request inputs are invalid."""


class FriendshipConflictError(ValueError):
    """Raised when a friendship for the same user pair already exists."""


class FriendshipNotFoundError(ValueError):
    """Raised when friendship record does not exist."""


class FriendshipPermissionError(ValueError):
    """Raised when actor has no permission for this friendship operation."""


class FriendshipStateError(ValueError):
    """Raised when friendship status does not match operation requirements."""


def _validate_friendship_pair(user_a: User, user_b: User) -> None:
    if user_a.id == user_b.id:
        raise FriendshipValidationError("friendship users must be different")


def _validate_request_message(request_message: str | None) -> None:
    if request_message is not None and len(request_message) > 200:
        raise FriendshipValidationError("request_message must be at most 200 characters")


def _validate_pagination(offset: int, limit: int) -> None:
    if offset < 0:
        raise FriendshipValidationError("offset must be greater than or equal to 0")
    if limit < 1 or limit > 100:
        raise FriendshipValidationError("limit must be in [1, 100]")


def _persist_friendship(session: Session, friendship: Friendship) -> Friendship:
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return friendship


def _delete_friendship(session: Session, friendship: Friendship) -> bool:
    session.delete(friendship)
    session.commit()
    return True


def _get_friendship_by_pair_key(
        session: Session,
        pair_key: str,
) -> Friendship | None:
    return session.exec(
        select(Friendship).where(Friendship.pair_key == pair_key)
    ).first()


def _get_friendship_by_pair(
        session: Session,
        user_a: User,
        user_b: User,
) -> Friendship | None:
    return _get_friendship_by_pair_key(
        session,
        Friendship.build_pair_key(user_a.id, user_b.id),
    )


def _require_directional_friendship(
        session: Session,
        *,
        requester: User,
        addressee: User,
) -> Friendship:
    _validate_friendship_pair(requester, addressee)
    friendship = _get_friendship_by_pair(session, requester, addressee)
    if friendship is None:
        raise FriendshipNotFoundError("friendship request not found")

    if friendship.requester_id != requester.id or friendship.addressee_id != addressee.id:
        raise FriendshipPermissionError("requester and addressee do not match friendship direction")

    return friendship


def _require_pending_directional_friendship(
        session: Session,
        *,
        requester: User,
        addressee: User,
) -> Friendship:
    friendship = _require_directional_friendship(
        session,
        requester=requester,
        addressee=addressee,
    )
    if friendship.status != FriendshipStatus.pending:
        raise FriendshipStateError("only pending friendship request can be processed")
    return friendship


def _list_friendships(
        session: Session,
        *filters,
        offset: int,
        limit: int,
) -> list[Friendship]:
    statement = (
        select(Friendship)
        .where(*filters)
        .order_by(desc(Friendship.created_at))
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def _change_pending_friendship_status(
        session: Session,
        *,
        requester: User,
        addressee: User,
        target_status: FriendshipStatus,
) -> Friendship:
    friendship = _require_pending_directional_friendship(
        session,
        requester=requester,
        addressee=addressee,
    )
    friendship.status = target_status
    friendship.accepted_at = (
        datetime.now(UTC)
        if target_status == FriendshipStatus.accepted
        else None
    )
    return _persist_friendship(session, friendship)


def get_friendship_between(
        session: Session,
        user_a: User,
        user_b: User,
) -> Friendship | None:
    _validate_friendship_pair(user_a, user_b)
    return _get_friendship_by_pair(session, user_a, user_b)


def create_friendship_request(
        session: Session,
        requester: User,
        addressee: User,
        *,
        request_message: str | None = None,
        source: FriendshipApplySource = FriendshipApplySource.search,
) -> Friendship:
    _validate_friendship_pair(requester, addressee)
    _validate_request_message(request_message)

    if is_blocked(session, requester, addressee):
        raise FriendshipValidationError("friendship request is blocked between these users")

    pair_key = Friendship.build_pair_key(requester.id, addressee.id)
    existing_friendship = _get_friendship_by_pair_key(session, pair_key)
    if existing_friendship is not None:
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


def accept_friendship_request(
        session: Session,
        *,
        addressee: User,
        requester: User,
) -> Friendship:
    return _change_pending_friendship_status(
        session,
        requester=requester,
        addressee=addressee,
        target_status=FriendshipStatus.accepted,
    )


def reject_friendship_request(
        session: Session,
        *,
        addressee: User,
        requester: User,
) -> Friendship:
    return _change_pending_friendship_status(
        session,
        requester=requester,
        addressee=addressee,
        target_status=FriendshipStatus.rejected,
    )


def cancel_friendship_request(
        session: Session,
        *,
        requester: User,
        addressee: User,
) -> bool:
    friendship = _require_pending_directional_friendship(
        session,
        requester=requester,
        addressee=addressee,
    )
    return _delete_friendship(session, friendship)


def unfriend(
        session: Session,
        *,
        user: User,
        friend: User,
) -> bool:
    _validate_friendship_pair(user, friend)
    friendship = _get_friendship_by_pair(session, user, friend)
    if friendship is None:
        raise FriendshipNotFoundError("friendship not found")
    if friendship.status != FriendshipStatus.accepted:
        raise FriendshipStateError("only accepted friendship can be removed")

    return _delete_friendship(session, friendship)


def list_incoming_pending_requests(
        session: Session,
        *,
        user: User,
        offset: int = 0,
        limit: int = 20,
) -> list[Friendship]:
    _validate_pagination(offset, limit)
    return _list_friendships(
        session,
        Friendship.addressee_id == user.id,
        Friendship.status == FriendshipStatus.pending,
        offset=offset,
        limit=limit,
    )


def list_outgoing_pending_requests(
        session: Session,
        *,
        user: User,
        offset: int = 0,
        limit: int = 20,
) -> list[Friendship]:
    _validate_pagination(offset, limit)
    return _list_friendships(
        session,
        Friendship.requester_id == user.id,
        Friendship.status == FriendshipStatus.pending,
        offset=offset,
        limit=limit,
    )


def list_accepted_friendships(
        session: Session,
        *,
        user: User,
        offset: int = 0,
        limit: int = 20,
) -> list[Friendship]:
    _validate_pagination(offset, limit)
    return _list_friendships(
        session,
        Friendship.status == FriendshipStatus.accepted,
        (Friendship.requester_id == user.id) | (Friendship.addressee_id == user.id),
        offset=offset,
        limit=limit,
    )
