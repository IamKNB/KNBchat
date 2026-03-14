from uuid import UUID

from sqlmodel import Session, col, select

from auth.user import User
from myapp.common.errors import raise_service_error
from myapp.modules.chat.schemas import Message, MessageRead
from myapp.modules.chat.services.pagination import apply_keyset_filter
from myapp.modules.chat.services.guards import require_conversation, require_member, require_message

from .pagination import KeysetAnchor, build_keyset_filter, decode_cursor, encode_cursor, validate_limit
from .repo import list_message_reads as list_message_reads_repo
from .types import DEFAULT_PAGE_LIMIT, MessagePage, MessageReadView

__all__ = [
    "send_message",
    "list_messages",
    "list_messages_with_senders",
    "mark_messages_read",
    "list_message_reads",
]

MESSAGE_MAX_LENGTH = 2000


def _validate_message_content(content: str) -> None:
    if not content or not content.strip():
        raise_service_error(
            status_code=400,
            code="message_bad_request",
            message="invalid message",
            detail="content must not be empty",
        )
    if len(content) > MESSAGE_MAX_LENGTH:
        raise_service_error(
            status_code=400,
            code="message_too_long",
            message="invalid message",
            detail=f"content must be at most {MESSAGE_MAX_LENGTH} characters",
        )


def send_message(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        content: str,
) -> Message:
    _validate_message_content(content)
    require_conversation(session, conversation_id)
    require_member(session, conversation_id=conversation_id, user_id=actor.id)

    message = Message(
        conversation_id=conversation_id,
        sender_id=actor.id,
        content=content,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def list_messages(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
) -> MessagePage:
    require_conversation(session, conversation_id)
    require_member(session, conversation_id=conversation_id, user_id=actor.id)
    validate_limit(limit)

    anchor = decode_cursor(cursor)

    statement = select(Message).where(Message.conversation_id == conversation_id)
    statement = apply_keyset_filter(statement, anchor, build_keyset_filter)

    statement = statement.order_by(
        col(Message.created_at).desc(),
        col(Message.id).desc(),
    ).limit(limit + 1)
    rows = list(session.exec(statement))
    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor: str | None = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor(KeysetAnchor(sort_time=last.created_at, message_id=last.id))

    return MessagePage(items=items, has_more=has_more, next_cursor=next_cursor)


def list_messages_with_senders(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
) -> tuple[MessagePage, dict[UUID, User]]:
    page = list_messages(
        session=session,
        actor=actor,
        conversation_id=conversation_id,
        cursor=cursor,
        limit=limit,
    )

    sender_ids = {item.sender_id for item in page.items}
    if not sender_ids:
        return page, {}

    senders = list(session.exec(select(User).where(col(User.id).in_(sender_ids))))
    senders_by_id = {sender.id: sender for sender in senders}

    if len(senders_by_id) != len(sender_ids):
        missing = sender_ids - set(senders_by_id.keys())
        raise_service_error(
            status_code=500,
            code="data_inconsistent",
            message="data inconsistent",
            detail=f"missing senders: {', '.join(str(item) for item in missing)}",
        )

    return page, senders_by_id


def mark_messages_read(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        message_ids: list[UUID],
) -> list[UUID]:
    if not message_ids:
        return []

    require_conversation(session, conversation_id)
    require_member(session, conversation_id=conversation_id, user_id=actor.id)

    unique_ids = list(dict.fromkeys(message_ids))
    rows = list(
        session.exec(
            select(Message).where(
                Message.conversation_id == conversation_id,
                col(Message.id).in_(unique_ids),
            )
        )
    )
    found_ids = {row.id for row in rows}
    missing = [str(message_id) for message_id in unique_ids if message_id not in found_ids]
    if missing:
        raise_service_error(
            status_code=404,
            code="message_not_found",
            message="message not found",
            detail=", ".join(missing),
        )

    for message_id in unique_ids:
        existing = session.get(MessageRead, (message_id, actor.id))
        if existing is not None:
            continue
        session.add(MessageRead(message_id=message_id, reader_id=actor.id))

    session.commit()
    return unique_ids


def list_message_reads(
        session: Session,
        *,
        actor: User,
        message_id: UUID,
) -> list[MessageReadView]:
    message = require_message(session, message_id)
    require_member(session, conversation_id=message.conversation_id, user_id=actor.id)

    reads = list_message_reads_repo(session, message_id)
    if not reads:
        return []

    reader_ids = {read.reader_id for read in reads}
    readers = list(session.exec(select(User).where(col(User.id).in_(reader_ids))))
    readers_by_id = {reader.id: reader for reader in readers}

    results: list[MessageReadView] = []
    for read in reads:
        reader = readers_by_id.get(read.reader_id)
        if reader is None:
            raise_service_error(
                status_code=500,
                code="data_inconsistent",
                message="data inconsistent",
                detail=f"missing reader {read.reader_id}",
            )
        results.append(MessageReadView(message_id=message_id, reader=reader, read_at=read.read_at))
    return results
