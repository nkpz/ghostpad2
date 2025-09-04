"""
Messages API router for Ghostpad.

Handles message editing and deletion operations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_service import chat_service

router = APIRouter()

# Pydantic models
class MessageUpdateRequest(BaseModel):
    content: str

class MessageUpdateResponse(BaseModel):
    id: int
    content: str
    updated_at: str


@router.put("/api/messages/{message_id}", response_model=MessageUpdateResponse)
async def update_message(message_id: int, data: MessageUpdateRequest):
    """Update a message's content"""
    try:
        result = await chat_service.update_message(message_id, data.content)
        return MessageUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")


@router.delete("/api/messages/{message_id}")
async def delete_message(message_id: int):
    """Delete a message and its attachments"""
    try:
        result = await chat_service.delete_message(message_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")