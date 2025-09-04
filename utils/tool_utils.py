"""
Shared utilities for tools.
"""

from dataclasses import dataclass

from services.data_access_service import with_db_session
from models import Message, MessageAttachment
from services.chat_service import chat_service, replace_message_placeholders


@dataclass
class ResponseChunk:
    type: str
    content: str


def assistant_chunk(content: str) -> ResponseChunk:
    return ResponseChunk("assistant", content)


def system_chunk(content: str) -> ResponseChunk:
    return ResponseChunk("system", content)


@with_db_session
async def create_system_message_in_conversation(
    message_content: str, conversation_id: str, session
):
    """Create a system message and attach it to a conversation."""

    processed_content = await replace_message_placeholders(
        message_content, conversation_id
    )
    # Create system message
    system_message = Message(content=processed_content, role="system")
    session.add(system_message)
    await session.commit()
    await session.refresh(system_message)

    # Get next sequence order and attach to conversation
    sequence_order = await chat_service._get_next_sequence_order(
        session, conversation_id
    )
    system_attachment = MessageAttachment(
        message_id=system_message.id,
        entity_type="conversation",
        entity_id=conversation_id,
        sequence_order=sequence_order,
    )
    session.add(system_attachment)
    await session.commit()

    return system_message.id
