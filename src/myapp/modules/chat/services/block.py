from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from auth.user import User
from myapp.modules.chat.schemas import UserBlock

__all__ = [
    "BlockValidationError",
    "block_user",
    "unblock_user",
    "is_blocked",
]


class BlockValidationError(ValueError):
    """Raised when block request inputs are invalid."""


def block_user(
        session: Session,
        blocker: User,
        blocked: User,
        *,
        reason: str | None = None,
) -> UserBlock:
    if blocker.id == blocked.id:
        raise BlockValidationError("blocker and blocked must be different")

    if reason is not None and len(reason) > 200:
        raise BlockValidationError("reason must be at most 200 characters")

    existing: UserBlock | None = session.get(UserBlock, (blocker.id, blocked.id))
    if existing is not None:
        existing.reason = reason
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    block = UserBlock(
        blocker_id=blocker.id,
        blocked_id=blocked.id,
        reason=reason,
    )
    session.add(block)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # Idempotent under concurrent requests.
        existing = session.get(UserBlock, (blocker.id, blocked.id))
        if existing is not None:
            existing.reason = reason
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        raise

    session.refresh(block)
    return block


def unblock_user(
        session: Session,
        blocker: User,
        blocked: User,
) -> bool:
    block = session.get(UserBlock, (blocker.id, blocked.id))
    if block is None:
        return False

    session.delete(block)
    session.commit()
    return True


def is_blocked(
        session: Session,
        user_a: User,
        user_b: User,
) -> bool:
    return (
            session.get(UserBlock, (user_a.id, user_b.id)) is not None
            or session.get(UserBlock, (user_b.id, user_a.id)) is not None
    )
