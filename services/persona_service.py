"""
Persona service for managing AI personas.

This service handles:
- Persona CRUD operations
- Avatar and metadata handling
- Persona validation and management
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select, delete

from utils.constants import ERROR_PERSONA_NOT_FOUND

from .data_access_service import with_db_session
from models import Persona, Conversation, ConversationPersona, MessageAttachment


class PersonaService:
    """Service for managing AI personas."""

    @with_db_session
    async def list_personas(self, session) -> List[Dict[str, Any]]:
        """List all personas."""
        stmt = select(Persona).order_by(Persona.updated_at.desc())
        result = await session.execute(stmt)
        personas = []
        for persona in result.scalars():
            personas.append(
                {
                    "id": persona.id,
                    "name": persona.name,
                    "description": persona.description,
                    "avatar_url": persona.avatar_url,
                    "created_at": (
                        persona.created_at.isoformat() if persona.created_at else None
                    ),
                    "updated_at": (
                        persona.updated_at.isoformat() if persona.updated_at else None
                    ),
                }
            )

        return personas

    @with_db_session
    async def get_persona(self, persona_id: int, session) -> Dict[str, Any]:
        """Get a single persona."""
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await session.execute(stmt)
        persona = result.scalar_one_or_none()

        if not persona:
            raise ValueError(ERROR_PERSONA_NOT_FOUND)

        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "avatar_url": persona.avatar_url,
            "created_at": (
                persona.created_at.isoformat() if persona.created_at else None
            ),
            "updated_at": (
                persona.updated_at.isoformat() if persona.updated_at else None
            ),
        }

    @with_db_session
    async def create_persona(
        self,
        name: str,
        session,
        description: str = None,
        avatar_url: str = None,
    ) -> Dict[str, Any]:
        """Create a new persona."""
        persona = Persona(
            name=name,
            description=description,
            avatar_url=avatar_url,
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "avatar_url": persona.avatar_url,
            "created_at": (
                persona.created_at.isoformat() if persona.created_at else None
            ),
            "updated_at": (
                persona.updated_at.isoformat() if persona.updated_at else None
            ),
        }

    @with_db_session
    async def update_persona(
        self,
        persona_id: int,
        session,
        name: str = None,
        description: str = None,
        avatar_url: str = None,
    ) -> Dict[str, Any]:
        """Update an existing persona."""
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await session.execute(stmt)
        persona = result.scalar_one_or_none()

        if not persona:
            raise ValueError(ERROR_PERSONA_NOT_FOUND)

        # Update provided fields
        if name is not None:
            persona.name = name
        if description is not None:
            persona.description = description
        if avatar_url is not None:
            persona.avatar_url = avatar_url

        await session.commit()
        await session.refresh(persona)

        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "avatar_url": persona.avatar_url,
            "created_at": (
                persona.created_at.isoformat() if persona.created_at else None
            ),
            "updated_at": (
                persona.updated_at.isoformat() if persona.updated_at else None
            ),
        }

    @with_db_session
    async def delete_persona(
        self, persona_id: int, session, delete_conversations: bool = False
    ) -> Dict[str, Any]:
        """Delete a persona and optionally its associated conversations."""
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await session.execute(stmt)
        persona = result.scalar_one_or_none()

        if not persona:
            raise ValueError(ERROR_PERSONA_NOT_FOUND)

        deleted_conversations_count = 0

        if delete_conversations:
            # Get all conversations that include this persona

            conversations_stmt = (
                select(Conversation.id)
                .join(ConversationPersona)
                .where(ConversationPersona.persona_id == persona_id)
            )
            conversations_result = await session.execute(conversations_stmt)
            conversation_ids = [conv_id for conv_id, in conversations_result]
            deleted_conversations_count = len(conversation_ids)

            # Delete conversations directly using bulk delete to avoid relationship issues
            if conversation_ids:
                # First delete ConversationPersona relationships for these conversations
                await session.execute(
                    delete(ConversationPersona).where(
                        ConversationPersona.conversation_id.in_(conversation_ids)
                    )
                )

                # Delete message attachments for these conversations
                await session.execute(
                    delete(MessageAttachment).where(
                        MessageAttachment.entity_type == "conversation",
                        MessageAttachment.entity_id.in_(conversation_ids),
                    )
                )

                # Delete conversations
                await session.execute(
                    delete(Conversation).where(Conversation.id.in_(conversation_ids))
                )
        else:
            # Just delete ConversationPersona relationships for this persona
            await session.execute(
                delete(ConversationPersona).where(
                    ConversationPersona.persona_id == persona_id
                )
            )

        # Delete the persona
        await session.delete(persona)
        await session.commit()

        return {
            "message": "Persona deleted successfully",
            "deleted_id": persona_id,
            "deleted_conversations": deleted_conversations_count,
        }

    @with_db_session
    async def validate_persona_name(
        self, name: str, session, exclude_id: int = None
    ) -> bool:
        """Check if a persona name is available."""
        stmt = select(Persona).where(Persona.name == name)
        if exclude_id:
            stmt = stmt.where(Persona.id != exclude_id)

        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        return existing is None

    @with_db_session
    async def search_personas(self, session, query: str) -> List[Dict[str, Any]]:
        """Search personas by name or description."""
        stmt = (
            select(Persona)
            .where(
                Persona.name.ilike(f"%{query}%")
                | Persona.description.ilike(f"%{query}%")
            )
            .order_by(Persona.updated_at.desc())
        )

        result = await session.execute(stmt)
        personas = []
        for persona in result.scalars():
            personas.append(
                {
                    "id": persona.id,
                    "name": persona.name,
                    "description": persona.description,
                    "avatar_url": persona.avatar_url,
                    "created_at": (
                        persona.created_at.isoformat() if persona.created_at else None
                    ),
                    "updated_at": (
                        persona.updated_at.isoformat() if persona.updated_at else None
                    ),
                }
            )

        return personas

    @with_db_session
    async def get_persona_names_for_conversation(
        self, conversation_id: str, session
    ) -> List[str]:
        """Get the persona names for a given conversation."""
        if conversation_id is None:
            return []
        stmt = (
            select(Persona.name)
            .join(ConversationPersona)
            .where(ConversationPersona.conversation_id == conversation_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


# Global persona service instance
persona_service = PersonaService()
