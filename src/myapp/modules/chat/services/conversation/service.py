from uuid import UUID

from sqlmodel import Session, col, select

from auth.user import User
from myapp.common.errors import raise_service_error
from myapp.modules.chat.schemas import (
    Conversation,
    ConversationMember,
    ConversationMemberRole,
    ConversationType,
)
from myapp.modules.chat.services.guards import (
    list_other_members,
    require_conversation,
    require_friendship_accepted,
    require_member,
    require_not_blocked,
    require_owner,
    require_user_exists,
)
from myapp.modules.chat.services.friendship.repo import normalize_pair_ids
from myapp.modules.chat.services.pagination import apply_keyset_filter

from .pagination import KeysetAnchor, build_keyset_filter, decode_cursor, encode_cursor, validate_limit
from .repo import get_direct_conversation_by_pair
from .types import ConversationBundle, ConversationPage, DEFAULT_PAGE_LIMIT

__all__ = [
    "create_or_get_direct_conversation",
    "create_group_conversation",
    "list_conversations",
    "invite_group_members",
    "remove_group_member",
    "leave_group",
]


def _ensure_member(
        session: Session,
        *,
        conversation_id: UUID,
        user_id: UUID,
        role: ConversationMemberRole,
) -> None:
    existing = session.get(ConversationMember, (conversation_id, user_id))
    if existing is not None:
        return
    session.add(
        ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
        )
    )


def create_or_get_direct_conversation(
        session: Session,
        *,
        actor: User,
        peer_id: UUID,
) -> ConversationBundle:
    if actor.id == peer_id:
        raise_service_error(
            status_code=400,
            code="conversation_bad_request",
            message="invalid conversation request",
            detail="peer must be different from actor",
        )
    peer = require_user_exists(session, peer_id)
    require_not_blocked(session, actor.id, peer_id)
    require_friendship_accepted(session, actor.id, peer_id)

    pair_low_id, pair_high_id = normalize_pair_ids(actor.id, peer_id)
    conversation = get_direct_conversation_by_pair(
        session,
        pair_low_id=pair_low_id,
        pair_high_id=pair_high_id,
    )

    if conversation is None:
        conversation = Conversation(
            type=ConversationType.direct,
            created_by=actor.id,
            pair_low_id=pair_low_id,
            pair_high_id=pair_high_id,
        )
        session.add(conversation)

    _ensure_member(
        session,
        conversation_id=conversation.id,
        user_id=actor.id,
        role=ConversationMemberRole.owner,
    )
    _ensure_member(
        session,
        conversation_id=conversation.id,
        user_id=peer_id,
        role=ConversationMemberRole.member,
    )

    session.commit()
    session.refresh(conversation)
    return ConversationBundle(conversation=conversation, peer=peer)


def create_group_conversation(
        session: Session,
        *,
        actor: User,
        name: str | None,
        member_ids: list[UUID],
) -> ConversationBundle:
    unique_members = list(dict.fromkeys(member_ids))
    unique_members = [member_id for member_id in unique_members if member_id != actor.id]

    for member_id in unique_members:
        require_user_exists(session, member_id)
        require_not_blocked(session, actor.id, member_id)
        require_friendship_accepted(session, actor.id, member_id)

    conversation = Conversation(
        type=ConversationType.group,
        name=name,
        created_by=actor.id,
    )
    session.add(conversation)

    session.add(
        ConversationMember(
            conversation_id=conversation.id,
            user_id=actor.id,
            role=ConversationMemberRole.owner,
        )
    )

    for member_id in unique_members:
        session.add(
            ConversationMember(
                conversation_id=conversation.id,
                user_id=member_id,
                role=ConversationMemberRole.member,
            )
        )

    session.commit()
    session.refresh(conversation)
    return ConversationBundle(conversation=conversation, peer=None)


def list_conversations(
        session: Session,
        *,
        actor: User,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
) -> ConversationPage:
    validate_limit(limit)
    anchor = decode_cursor(cursor)

    statement = (
        select(Conversation)
        .join(ConversationMember)
        .where(ConversationMember.user_id == actor.id)
    )
    statement = apply_keyset_filter(statement, anchor, build_keyset_filter)

    statement = statement.order_by(
        col(Conversation.created_at).desc(),
        col(Conversation.id).desc(),
    ).limit(limit + 1)

    rows = list(session.exec(statement))
    has_more = len(rows) > limit
    conversations = rows[:limit]
    if not conversations:
        return ConversationPage(items=[], has_more=False, next_cursor=None)

    direct_ids = [conversation.id for conversation in conversations if conversation.type == ConversationType.direct]
    peers_by_conversation: dict[UUID, User] = {}
    if direct_ids:
        members = list(
            session.exec(
                select(ConversationMember).where(
                    col(ConversationMember.conversation_id).in_(direct_ids),
                    ConversationMember.user_id != actor.id,
                ),
            )
        )
        peer_ids = {member.user_id for member in members}
        if peer_ids:
            peers = list(session.exec(select(User).where(col(User.id).in_(peer_ids))))
            peers_by_id = {peer.id: peer for peer in peers}
            for member in members:
                peer = peers_by_id.get(member.user_id)
                if peer is not None:
                    peers_by_conversation[member.conversation_id] = peer

    bundles: list[ConversationBundle] = []
    for conversation in conversations:
        peer = peers_by_conversation.get(conversation.id)
        bundles.append(ConversationBundle(conversation=conversation, peer=peer))

    next_cursor: str | None = None
    if has_more and bundles:
        last = bundles[-1].conversation
        next_cursor = encode_cursor(
            KeysetAnchor(
                sort_time=last.created_at,
                conversation_id=last.id,
            )
        )

    return ConversationPage(
        items=bundles,
        has_more=has_more,
        next_cursor=next_cursor,
    )


def invite_group_members(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        member_ids: list[UUID],
) -> list[UUID]:
    conversation = require_conversation(session, conversation_id)
    if conversation.type != ConversationType.group:
        raise_service_error(
            status_code=409,
            code="conversation_state_conflict",
            message="conversation state conflict",
            detail="only group conversation can add members",
        )

    require_owner(session, conversation_id=conversation_id, user_id=actor.id)

    unique_members = list(dict.fromkeys(member_ids))
    unique_members = [member_id for member_id in unique_members if member_id != actor.id]

    added: list[UUID] = []
    for member_id in unique_members:
        require_user_exists(session, member_id)
        require_not_blocked(session, actor.id, member_id)
        require_friendship_accepted(session, actor.id, member_id)

        existing = session.get(ConversationMember, (conversation_id, member_id))
        if existing is not None:
            continue
        session.add(
            ConversationMember(
                conversation_id=conversation_id,
                user_id=member_id,
                role=ConversationMemberRole.member,
            )
        )
        added.append(member_id)

    if added:
        session.commit()
    return added


def remove_group_member(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
        member_id: UUID,
) -> UUID:
    conversation = require_conversation(session, conversation_id)
    if conversation.type != ConversationType.group:
        raise_service_error(
            status_code=409,
            code="conversation_state_conflict",
            message="conversation state conflict",
            detail="only group conversation can remove members",
        )

    require_owner(session, conversation_id=conversation_id, user_id=actor.id)

    target = session.get(ConversationMember, (conversation_id, member_id))
    if target is None:
        raise_service_error(
            status_code=404,
            code="conversation_member_not_found",
            message="conversation member not found",
            detail=str(member_id),
        )
    if target.role == ConversationMemberRole.owner:
        raise_service_error(
            status_code=409,
            code="conversation_state_conflict",
            message="conversation state conflict",
            detail="owner cannot be removed",
        )

    session.delete(target)
    session.commit()
    return member_id


def leave_group(
        session: Session,
        *,
        actor: User,
        conversation_id: UUID,
) -> UUID:
    conversation = require_conversation(session, conversation_id)
    if conversation.type != ConversationType.group:
        raise_service_error(
            status_code=409,
            code="conversation_state_conflict",
            message="conversation state conflict",
            detail="only group conversation can be left",
        )

    member = require_member(session, conversation_id=conversation_id, user_id=actor.id)
    if member.role == ConversationMemberRole.owner:
        others = list_other_members(session, conversation_id=conversation_id, user_id=actor.id)
        if others:
            raise_service_error(
                status_code=409,
                code="conversation_state_conflict",
                message="conversation state conflict",
                detail="owner cannot leave while other members remain",
            )

    session.delete(member)
    session.commit()
    return actor.id
