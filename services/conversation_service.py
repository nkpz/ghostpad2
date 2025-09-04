"""
Conversation service for managing conversations and message attachments.

This service handles:
- Conversation CRUD operations
- Message attachment handling
- Conversation-persona relationships
- Conversation history and metadata
"""

from typing import Dict, Any, List, Optional, Union
from sqlalchemy import select, func, delete, or_

from .data_access_service import with_db_session
from models import Conversation, Message, MessageAttachment, Persona, ConversationPersona
from .ai_service import ai_service
from .kv_store_service import kv_store


class ConversationService:
    """Service for managing conversations."""
    
    
    @with_db_session
    async def get_all_conversations(self, session) -> List[Dict[str, Any]]:
        """Get all conversations with message counts."""
        # Get conversations with message counts
        stmt = select(
            Conversation,
            func.count(MessageAttachment.id).label('message_count')
        ).outerjoin(
            MessageAttachment,
            (MessageAttachment.entity_type == 'conversation') & 
            (MessageAttachment.entity_id == Conversation.id)
        ).group_by(Conversation.id).order_by(Conversation.updated_at.desc())
        
        result = await session.execute(stmt)
        conversations = []
        
        for conv, msg_count in result:
            conversations.append({
                "id": conv.id,
                "title": conv.title or f"Conversation {conv.id}",
                "created_at": conv.created_at.isoformat(),
                "message_count": msg_count or 0
            })
        
        return conversations
    
    @with_db_session
    async def get_conversation_by_id(self, conversation_id: str, session) -> Optional[Dict[str, Any]]:
        """Get a single conversation by UUID."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            # Get message count
            msg_count_stmt = select(func.count(MessageAttachment.id)).where(
                (MessageAttachment.entity_type == 'conversation') & 
                (MessageAttachment.entity_id == conversation.id)
            )
            msg_count_result = await session.execute(msg_count_stmt)
            msg_count = msg_count_result.scalar_one()

            return {
                "id": conversation.id,
                "title": conversation.title or f"Conversation {conversation.id}",
                "created_at": conversation.created_at.isoformat(),
                "message_count": msg_count or 0
            }
        return None
    
    @with_db_session
    async def create_conversation(self, title: str = None, persona_ids: List[int] = None, session=None) -> Dict[str, Any]:
        """Create a new conversation."""
        conversation = Conversation(
            title=title or "New Conversation"
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

        # Attach provided persona ids if present, otherwise attach default assistant persona (first persona in DB)
        try:
            if persona_ids:
                for pid in persona_ids:
                    try:
                        cp = ConversationPersona(conversation_id=conversation.id, persona_id=int(pid))
                        session.add(cp)
                    except Exception:
                        await session.rollback()
                await session.commit()
            else:
                stmt = select(Persona).order_by(Persona.id.asc())
                result = await session.execute(stmt)
                default_persona = result.scalars().first()
                if default_persona:
                    cp = ConversationPersona(conversation_id=conversation.id, persona_id=default_persona.id)
                    session.add(cp)
                    await session.commit()
        except Exception:
            # Non-fatal: continue even if persona attachment fails
            try:
                await session.rollback()
            except Exception:
                pass

        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "message_count": 0
        }
    
    @with_db_session
    async def get_conversation_messages(self, conversation_id: str, session) -> Dict[str, Any]:
        """Get all messages in a conversation along with active personas."""
        # Messages with sequence_order
        stmt = select(Message, MessageAttachment.sequence_order).join(MessageAttachment).where(
            MessageAttachment.entity_type == 'conversation',
            MessageAttachment.entity_id == conversation_id
        ).order_by(MessageAttachment.sequence_order)

        result = await session.execute(stmt)
        messages = []

        for message, sequence_order in result:
            messages.append({
                "id": message.id,
                "content": message.content,
                "role": message.role,
                "created_at": message.created_at.isoformat(),
                "conversation_id": conversation_id,
                "sequence_order": sequence_order
            })

        # Active personas for this conversation
        personas_stmt = select(Persona).join(ConversationPersona).where(ConversationPersona.conversation_id == conversation_id)
        personas_result = await session.execute(personas_stmt)
        personas = []
        for p in personas_result.scalars():
            personas.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "avatar_url": p.avatar_url,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })

        return {"messages": messages, "personas": personas}
    
    @with_db_session
    async def delete_conversation(self, conversation_id: str, session) -> Dict[str, Any]:
        """Delete a conversation and all its message attachments."""
        # Check if conversation exists
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        # Delete any conversation-persona junction rows first to avoid NULLing behavior
        try:
            await session.execute(delete(ConversationPersona).where(ConversationPersona.conversation_id == conversation_id))
        except Exception:
            # Non-fatal; continue to delete conversation
            await session.rollback()

        # Delete the conversation (cascade will handle message attachments)
        await session.delete(conversation)
        await session.commit()
        
        # Clean up k/v store entries for this conversation
        try:
            deleted_count = await kv_store.delete_keys_containing(conversation_id)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} k/v entries for conversation {conversation_id}")
        except Exception as e:
            print(f"Warning: Failed to clean up k/v entries for conversation {conversation_id}: {e}")

        return {"message": "Conversation deleted successfully"}
    
    @with_db_session
    async def add_persona_to_conversation(self, conversation_id: str, persona_id: int, session) -> Dict[str, Any]:
        """Attach a persona to a conversation."""
        # Check conversation exists
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")

        # Check persona exists
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await session.execute(stmt)
        persona = result.scalar_one_or_none()
        if not persona:
            raise ValueError("Persona not found")

        # Create junction if not exists
        try:
            cp = ConversationPersona(conversation_id=conversation_id, persona_id=persona_id)
            session.add(cp)
            await session.commit()
        except Exception:
            # Could be unique constraint violation — ignore
            await session.rollback()

        return {"message": "Persona added to conversation"}
    
    @with_db_session
    async def remove_persona_from_conversation(self, conversation_id: str, persona_id: int, session) -> Dict[str, Any]:
        """Remove a persona from a conversation."""
        stmt = select(ConversationPersona).where(
            ConversationPersona.conversation_id == conversation_id,
            ConversationPersona.persona_id == persona_id
        )
        result = await session.execute(stmt)
        cp = result.scalar_one_or_none()
        if not cp:
            raise ValueError("Persona not attached to conversation")

        await session.delete(cp)
        await session.commit()

        return {"message": "Persona removed from conversation"}
    
    @with_db_session
    async def generate_title(self, conversation_id: str, user_message: str, assistant_message: str, session) -> str:
        """Generate a conversation title based on the first exchange."""
        try:
            generated_title = await ai_service.generate_title(user_message, assistant_message)
            
            # Update the conversation title in the database
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                conversation.title = generated_title
                await session.commit()
            
            return generated_title
        except Exception as e:
            print(f"Title generation failed: {str(e)}")
            return "New Chat"


conversation_service = ConversationService()