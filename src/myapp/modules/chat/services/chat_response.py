from uuid import UUID

from auth.user import User, User2Friends, User2Public
from myapp.common.errors import raise_service_error
from myapp.common.api import CursorMeta
from myapp.modules.chat.schemas import Message
from myapp.modules.chat.schemas.chat_api import (
    ConversationEnvelope,
    ConversationListEnvelope,
    ConversationMemberActionData,
    ConversationMemberActionEnvelope,
    ConversationSummary,
    MessageData,
    MessageEnvelope,
    MessageListEnvelope,
    ReadMessagesData,
    ReadMessagesEnvelope,
    ReadReceiptData,
    ReadReceiptListEnvelope,
)
from myapp.modules.chat.services.conversation.types import ConversationBundle, ConversationPage
from myapp.modules.chat.services.message.types import MessagePage, MessageReadView

__all__ = [
    "build_conversation_envelope",
    "build_conversation_list_envelope",
    "build_member_action_envelope",
    "build_message_envelope",
    "build_message_list_envelope",
    "build_read_messages_envelope",
    "build_read_receipt_list_envelope",
]


def _to_conversation_summary(bundle: ConversationBundle) -> ConversationSummary:
    peer_data = None
    if bundle.peer is not None:
        peer_data = User2Friends.model_validate(bundle.peer)
    conversation = bundle.conversation
    return ConversationSummary(
        id=conversation.id,
        type=conversation.type,
        name=conversation.name,
        created_at=conversation.created_at,
        created_by=conversation.created_by,
        peer=peer_data,
    )


def build_conversation_envelope(bundle: ConversationBundle, *, code: str, message: str) -> ConversationEnvelope:
    return ConversationEnvelope(
        code=code,
        message=message,
        data=_to_conversation_summary(bundle),
    )


def build_conversation_list_envelope(
        page: ConversationPage,
        *,
        code: str,
        message: str,
) -> ConversationListEnvelope:
    return ConversationListEnvelope(
        code=code,
        message=message,
        data=[_to_conversation_summary(bundle) for bundle in page.items],
        meta=CursorMeta(has_more=page.has_more, next_cursor=page.next_cursor),
    )


def build_member_action_envelope(
        *,
        conversation_id: UUID,
        member_ids: list[UUID],
        code: str,
        message: str,
) -> ConversationMemberActionEnvelope:
    return ConversationMemberActionEnvelope(
        code=code,
        message=message,
        data=ConversationMemberActionData(
            conversation_id=conversation_id,
            member_ids=member_ids,
        ),
    )


def _to_message_data(message: Message, *, sender: User) -> MessageData:
    return MessageData(
        id=message.id,
        conversation_id=message.conversation_id,
        content=message.content,
        created_at=message.created_at,
        sender=User2Public.model_validate(sender),
    )


def build_message_envelope(message: Message, *, sender: User, code: str, message_text: str) -> MessageEnvelope:
    return MessageEnvelope(
        code=code,
        message=message_text,
        data=_to_message_data(message, sender=sender),
    )


def build_message_list_envelope(
        page: MessagePage,
        *,
        senders_by_id: dict[UUID, User],
        code: str,
        message_text: str,
) -> MessageListEnvelope:
    data: list[MessageData] = []
    for item in page.items:
        sender = senders_by_id.get(item.sender_id)
        if sender is None:
            raise_service_error(
                status_code=500,
                code="data_inconsistent",
                message="data inconsistent",
                detail=f"missing sender {item.sender_id}",
            )
        data.append(_to_message_data(item, sender=sender))
    return MessageListEnvelope(
        code=code,
        message=message_text,
        data=data,
        meta=CursorMeta(
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        ),
    )


def build_read_messages_envelope(
        message_ids: list[UUID],
        *,
        code: str,
        message_text: str,
) -> ReadMessagesEnvelope:
    return ReadMessagesEnvelope(
        code=code,
        message=message_text,
        data=ReadMessagesData(message_ids=message_ids),
    )


def build_read_receipt_list_envelope(
        reads: list[MessageReadView],
        *,
        code: str,
        message_text: str,
) -> ReadReceiptListEnvelope:
    data = [
        ReadReceiptData(
            message_id=read.message_id,
            reader=User2Public.model_validate(read.reader),
            read_at=read.read_at,
        )
        for read in reads
    ]
    return ReadReceiptListEnvelope(
        code=code,
        message=message_text,
        data=data,
        meta=CursorMeta(has_more=False, next_cursor=None),
    )
