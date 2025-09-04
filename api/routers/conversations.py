"""
Conversations API router for Ghostpad.

Handles conversation CRUD operations, message retrieval, and persona management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.conversation_service import conversation_service

router = APIRouter()

# Pydantic models
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    persona_ids: List[int] | None = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int


@router.get("/api/conversations")
async def get_conversations():
    """Get all conversations with message counts"""
    try:
        conversations = await conversation_service.get_all_conversations()
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


@router.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(data: ConversationCreate):
    """Create a new conversation"""
    try:
        conversation = await conversation_service.create_conversation(
            title=data.title,
            persona_ids=data.persona_ids
        )
        return ConversationResponse(**conversation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a single conversation by ID"""
    try:
        conversation = await conversation_service.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationResponse(**conversation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation"""
    try:
        result = await conversation_service.get_conversation_messages(conversation_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its message attachments"""
    try:
        result = await conversation_service.delete_conversation(conversation_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/api/conversations/{conversation_id}/personas/{persona_id}")
async def add_persona_to_conversation(conversation_id: str, persona_id: int):
    """Attach a persona to a conversation"""
    try:
        result = await conversation_service.add_persona_to_conversation(conversation_id, persona_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add persona to conversation: {str(e)}")


@router.delete("/api/conversations/{conversation_id}/personas/{persona_id}")
async def remove_persona_from_conversation(conversation_id: str, persona_id: int):
    """Remove a persona from a conversation"""
    try:
        result = await conversation_service.remove_persona_from_conversation(conversation_id, persona_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove persona from conversation: {str(e)}")