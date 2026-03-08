from uuid import UUID

from sqlmodel import Session

from auth.user import User
from myapp.modules.chat.schemas import UserBlock

__all__ = [
    "BlockValidationError",
    "block_user",
    "unblock_user",
    "is_blocked",
    "is_blocked_by_ids",
]


class BlockValidationError(ValueError):
    """Raised when block request inputs are invalid."""


def _validate_block_pair(blocker: User, blocked: User) -> None:
    if blocker.id == blocked.id:
        raise BlockValidationError("blocker and blocked must be different")


def _validate_reason(reason: str | None) -> None:
    if reason is not None and len(reason) > 200:
        raise BlockValidationError("reason must be at most 200 characters")


def _get_block_by_ids(
        session: Session,
        blocker_id: UUID,
        blocked_id: UUID,
) -> UserBlock | None:
    return session.get(UserBlock, (blocker_id, blocked_id))


def _get_block(
        session: Session,
        blocker: User,
        blocked: User,
) -> UserBlock | None:
    return _get_block_by_ids(
        session,
        blocker.id,
        blocked.id,
    )


def _exists_block_by_ids(
        session: Session,
        blocker_id: UUID,
        blocked_id: UUID,
) -> bool:
    return session.get(UserBlock, (blocker_id, blocked_id)) is not None


def _persist_block(session: Session, block: UserBlock) -> UserBlock:
    session.add(block)
    session.commit()
    session.refresh(block)
    refreshed = _get_block_by_ids(
        session,
        block.blocker_id,
        block.blocked_id,
    )
    if refreshed is None:
        raise RuntimeError("block not found after persistence")
    return refreshed


def _update_block_reason(
        session: Session,
        block: UserBlock,
        reason: str | None,
) -> UserBlock:
    block.reason = reason
    return _persist_block(session, block)


def block_user(
        session: Session,
        blocker: User,
        blocked: User,
        *,
        reason: str | None = None,
) -> UserBlock:
    _validate_block_pair(blocker, blocked)
    _validate_reason(reason)

    existing = _get_block(session, blocker, blocked)
    if existing is not None:
        return _update_block_reason(session, existing, reason)

    block = UserBlock(
        blocker_id=blocker.id,
        blocked_id=blocked.id,
        reason=reason,
    )
    return _persist_block(session, block)


def unblock_user(
        session: Session,
        blocker: User,
        blocked: User,
) -> bool:
    block = _get_block(session, blocker, blocked)
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
    return is_blocked_by_ids(session, user_a.id, user_b.id)


def is_blocked_by_ids(
        session: Session,
        user_a_id: UUID,
        user_b_id: UUID,
) -> bool:
    return (
            _exists_block_by_ids(session, user_a_id, user_b_id)
            or _exists_block_by_ids(session, user_b_id, user_a_id)
    )
