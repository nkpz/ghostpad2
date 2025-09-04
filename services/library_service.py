"""
Library service for managing prompt snippets.

This service handles:
- Library snippet CRUD operations
- Snippet type filtering
- Content management
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select

from models import LibrarySnippet
from services.data_access_service import with_db_session


class LibraryService:
    """Service for managing library snippets."""

    @with_db_session
    async def list_snippets(
        self, session, snippet_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all library snippets, optionally filtered by type."""
        stmt = select(LibrarySnippet)
        if snippet_type:
            stmt = stmt.where(LibrarySnippet.type == snippet_type)
        stmt = stmt.order_by(LibrarySnippet.updated_at.desc())

        result = await session.execute(stmt)
        snippets = []
        for s in result.scalars():
            snippets.append(
                {
                    "id": s.id,
                    "type": s.type,
                    "name": s.name,
                    "content": s.content,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
            )
        return snippets

    @with_db_session
    async def get_snippet(self, snippet_id: int, session) -> Dict[str, Any]:
        """Get a single library snippet by ID."""
        stmt = select(LibrarySnippet).where(LibrarySnippet.id == snippet_id)
        result = await session.execute(stmt)
        s = result.scalar_one_or_none()

        if not s:
            raise ValueError("Snippet not found")

        return {
            "id": s.id,
            "type": s.type,
            "name": s.name,
            "content": s.content,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }

    @with_db_session
    async def create_snippet(
        self, snippet_type: str, name: str, content: str, session
    ) -> Dict[str, Any]:
        """Create a new library snippet."""
        if not snippet_type or not name or content is None:
            raise ValueError("type, name, and content are required")

        snippet = LibrarySnippet(type=snippet_type, name=name, content=content)
        session.add(snippet)
        await session.commit()
        await session.refresh(snippet)

        return {
            "id": snippet.id,
            "type": snippet.type,
            "name": snippet.name,
            "content": snippet.content,
            "created_at": (
                snippet.created_at.isoformat() if snippet.created_at else None
            ),
            "updated_at": (
                snippet.updated_at.isoformat() if snippet.updated_at else None
            ),
        }

    @with_db_session
    async def delete_snippet(self, snippet_id: int, session) -> Dict[str, Any]:
        """Delete a library snippet."""
        stmt = select(LibrarySnippet).where(LibrarySnippet.id == snippet_id)
        result = await session.execute(stmt)
        s = result.scalar_one_or_none()

        if not s:
            raise ValueError("Snippet not found")

        await session.delete(s)
        await session.commit()

        return {"message": "Snippet deleted"}


# Global library service instance
library_service = LibraryService()
