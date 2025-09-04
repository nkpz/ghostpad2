"""
Data Access Service for managing database connections and sessions.

This service handles:
- Database engine initialization
- Session factory management
- Database schema creation
- Session context management for other services
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import functools

from models import Base, Persona
from utils.constants import ERROR_DATA_ACCESS_NOT_INITIALIZED


class DataAccessService:
    """Singleton service for database access operations."""

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False

    async def initialize(self):
        """Initialize the database engine and session factory."""
        if self._initialized:
            return

        # Create async engine
        self._engine = create_async_engine("sqlite+aiosqlite:///conversations.db")

        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session factory
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        self._initialized = True

        # Seed default data
        await self._seed_default_persona()

    async def _seed_default_persona(self):
        """Seed a default Assistant persona if none exist."""
        try:
            async with self.get_session_context() as session:
                stmt = select(Persona).where(Persona.name == "Assistant")
                result = await session.execute(stmt)
                persona = result.scalar_one_or_none()
                if not persona:
                    default_persona = Persona(
                        name="Assistant",
                        description="Default assistant persona",
                        avatar_url=None,
                    )
                    session.add(default_persona)
                    await session.commit()
        except Exception:
            # Non-fatal: if seeding fails, continue without blocking startup
            pass

    def get_session_context(self):
        """Get a database session context manager for use in services."""
        if not self._initialized:
            raise RuntimeError(ERROR_DATA_ACCESS_NOT_INITIALIZED)
        return DatabaseSessionContext(self._session_factory)

    async def get_session_for_fastapi(self) -> AsyncGenerator[AsyncSession, None]:
        """Database session dependency for FastAPI routes."""
        if not self._initialized:
            raise RuntimeError(ERROR_DATA_ACCESS_NOT_INITIALIZED)

        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_engine(self):
        """Get the database engine."""
        if not self._initialized:
            raise RuntimeError(ERROR_DATA_ACCESS_NOT_INITIALIZED)
        return self._engine

    def get_session_factory(self):
        """Get the session factory."""
        if not self._initialized:
            raise RuntimeError(ERROR_DATA_ACCESS_NOT_INITIALIZED)
        return self._session_factory


class DatabaseSessionContext:
    """Async context manager for database sessions."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


# Global singleton instance
data_access_service = DataAccessService()


def with_db_session(func):
    """Decorator that provides a database session to the decorated method."""
    import inspect

    if inspect.isasyncgenfunction(func):
        # Handle async generators
        @functools.wraps(func)
        async def async_gen_wrapper(*args, **kwargs):
            async with data_access_service.get_session_context() as session:
                async for item in func(*args, session=session, **kwargs):
                    yield item

        return async_gen_wrapper
    else:
        # Handle regular async functions
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with data_access_service.get_session_context() as session:
                return await func(*args, session=session, **kwargs)

        return wrapper
