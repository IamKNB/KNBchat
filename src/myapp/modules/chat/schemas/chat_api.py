from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from auth.user import User2Friends, User2Public
from myapp.common.api import Envelope, ListEnvelope
from .conversation import ConversationMemberRole, ConversationType

__all__ = [
    "CreateDirectConversationBody",
    "CreateGroupConversationBody",
    "InviteMembersBody",
    "ConversationSummary",
    "ConversationEnvelope",
    "ConversationListEnvelope",
    "ConversationMemberActionData",
    "ConversationMemberActionEnvelope",
    "SendMessageBody",
    "MessageData",
    "MessageEnvelope",
    "MessageListEnvelope",
    "ReadMessagesBody",
    "ReadMessagesData",
    "ReadMessagesEnvelope",
    "ReadReceiptData",
    "ReadReceiptListEnvelope",
    "ConversationType",
    "ConversationMemberRole",
]


class CreateDirectConversationBody(SQLModel):
    peer_id: UUID


class CreateGroupConversationBody(SQLModel):
    name: str | None = None
    member_ids: list[UUID] = Field(default_factory=list)


class InviteMembersBody(SQLModel):
    member_ids: list[UUID] = Field(default_factory=list)


class ConversationSummary(SQLModel):
    id: UUID
    type: ConversationType
    name: str | None = None
    created_at: datetime
    created_by: UUID
    peer: User2Friends | None = None


class ConversationMemberActionData(SQLModel):
    conversation_id: UUID
    member_ids: list[UUID]


class SendMessageBody(SQLModel):
    content: str


class MessageData(SQLModel):
    id: UUID
    conversation_id: UUID
    content: str
    created_at: datetime
    sender: User2Public


class ReadMessagesBody(SQLModel):
    message_ids: list[UUID] = Field(default_factory=list)


class ReadMessagesData(SQLModel):
    message_ids: list[UUID]


class ReadReceiptData(SQLModel):
    message_id: UUID
    reader: User2Public
    read_at: datetime


ConversationEnvelope = Envelope[ConversationSummary]
ConversationListEnvelope = ListEnvelope[ConversationSummary]
ConversationMemberActionEnvelope = Envelope[ConversationMemberActionData]
MessageEnvelope = Envelope[MessageData]
MessageListEnvelope = ListEnvelope[MessageData]
ReadMessagesEnvelope = Envelope[ReadMessagesData]
ReadReceiptListEnvelope = ListEnvelope[ReadReceiptData]
