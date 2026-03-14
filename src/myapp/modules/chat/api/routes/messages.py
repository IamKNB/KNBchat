from uuid import UUID

from fastapi import APIRouter, Depends

from auth import get_user
from auth.user import User
from db import SessionDep
from myapp.common.api import PaginationParams
from myapp.modules.chat.api.errors.chat import CHAT_ERROR_RESPONSES, ChatRoute
from myapp.modules.chat.schemas.chat_api import (
    MessageEnvelope,
    MessageListEnvelope,
    ReadMessagesBody,
    ReadMessagesEnvelope,
    ReadReceiptListEnvelope,
    SendMessageBody,
)
from myapp.modules.chat.services.chat_response import (
    build_message_envelope,
    build_message_list_envelope,
    build_read_messages_envelope,
    build_read_receipt_list_envelope,
)
from myapp.modules.chat.services.message.service import (
    list_message_reads,
    list_messages_with_senders,
    mark_messages_read,
    send_message,
)

__all__ = ["router"]

router = APIRouter(
    tags=["messages"],
    route_class=ChatRoute,
    responses=CHAT_ERROR_RESPONSES,
)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageEnvelope)
def create_message(
        conversation_id: UUID,
        body: SendMessageBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> MessageEnvelope:
    message = send_message(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
        content=body.content,
    )
    return build_message_envelope(
        message,
        sender=current_user,
        code="message_sent",
        message_text="message sent",
    )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListEnvelope)
def list_messages_route(
        conversation_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
        pagination: PaginationParams = Depends(),
) -> MessageListEnvelope:
    page, senders_by_id = list_messages_with_senders(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )

    return build_message_list_envelope(
        page,
        senders_by_id=senders_by_id,
        code="messages_listed",
        message_text="messages listed",
    )


@router.post("/conversations/{conversation_id}/messages/read", response_model=ReadMessagesEnvelope)
def mark_messages_read_route(
        conversation_id: UUID,
        body: ReadMessagesBody,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ReadMessagesEnvelope:
    message_ids = mark_messages_read(
        session=session,
        actor=current_user,
        conversation_id=conversation_id,
        message_ids=body.message_ids,
    )
    return build_read_messages_envelope(
        message_ids,
        code="messages_read",
        message_text="messages read",
    )


@router.get("/messages/{message_id}/reads", response_model=ReadReceiptListEnvelope)
def list_message_reads_route(
        message_id: UUID,
        session: SessionDep,
        current_user: User = Depends(get_user),
) -> ReadReceiptListEnvelope:
    reads = list_message_reads(
        session=session,
        actor=current_user,
        message_id=message_id,
    )
    return build_read_receipt_list_envelope(
        reads,
        code="message_reads_listed",
        message_text="message reads listed",
    )
