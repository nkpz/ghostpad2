"""
Personas API router for Ghostpad.

Handles persona CRUD operations and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.persona_service import persona_service

router = APIRouter()

# Pydantic models
class PersonaCreate(BaseModel):
    name: str
    description: str = None
    avatar_url: str = None

class PersonaResponse(BaseModel):
    id: int
    name: str
    description: str = None
    avatar_url: str = None
    created_at: str
    updated_at: str

class PersonaUpdate(BaseModel):
    name: str = None
    description: str = None
    avatar_url: str = None


@router.get("/api/personas")
async def list_personas():
    """List all personas"""
    try:
        personas = await persona_service.list_personas()
        return {"personas": personas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list personas: {str(e)}")


@router.get("/api/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: int):
    """Get a single persona"""
    try:
        persona = await persona_service.get_persona(persona_id)
        return PersonaResponse(**persona)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get persona: {str(e)}")


@router.post("/api/personas", response_model=PersonaResponse)
async def create_persona(data: PersonaCreate):
    """Create a new persona"""
    try:
        persona = await persona_service.create_persona(
            name=data.name,
            description=data.description,
            avatar_url=data.avatar_url
        )
        return PersonaResponse(**persona)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")


@router.put("/api/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: int, data: PersonaUpdate):
    """Update an existing persona"""
    try:
        persona = await persona_service.update_persona(
            persona_id=persona_id,
            name=data.name,
            description=data.description,
            avatar_url=data.avatar_url
        )
        return PersonaResponse(**persona)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update persona: {str(e)}")


@router.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: int, delete_conversations: bool = False):
    """Delete a persona and optionally its associated conversations"""
    try:
        result = await persona_service.delete_persona(persona_id, delete_conversations)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete persona: {str(e)}")