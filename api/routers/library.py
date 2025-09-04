"""
Library API router for Ghostpad.

Handles library snippet CRUD operations for reusable prompt components.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.library_service import library_service

router = APIRouter()

# Pydantic models
class LibrarySnippetCreate(BaseModel):
    type: str
    name: str
    content: str

class LibrarySnippetResponse(BaseModel):
    id: int
    type: str
    name: str
    content: str
    created_at: str
    updated_at: str


@router.get('/api/library')
async def list_library_snippets(type: Optional[str] = Query(None)):
    """List all library snippets, optionally filtered by type."""
    try:
        snippets = await library_service.list_snippets(snippet_type=type)
        return {'snippets': snippets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list library snippets: {str(e)}")


@router.post('/api/library', response_model=LibrarySnippetResponse)
async def create_library_snippet(data: LibrarySnippetCreate):
    """Create a new library snippet."""
    try:
        snippet = await library_service.create_snippet(
            snippet_type=data.type,
            name=data.name,
            content=data.content
        )
        return LibrarySnippetResponse(**snippet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create library snippet: {str(e)}")


@router.get('/api/library/{snippet_id}', response_model=LibrarySnippetResponse)
async def get_library_snippet(snippet_id: int):
    """Get a single library snippet by ID."""
    try:
        snippet = await library_service.get_snippet(snippet_id)
        return LibrarySnippetResponse(**snippet)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get library snippet: {str(e)}")


@router.delete('/api/library/{snippet_id}')
async def delete_library_snippet(snippet_id: int):
    """Delete a library snippet."""
    try:
        result = await library_service.delete_snippet(snippet_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete library snippet: {str(e)}")