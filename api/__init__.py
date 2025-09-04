"""
API package for Ghostpad.

This package provides:
- FastAPI application configuration and setup
- API routers for all endpoints
- Middleware for CORS, error handling, and security
- Dependencies for database sessions and service injection
- Application configuration and settings management
"""

from .config import settings, constants
from .middleware import setup_all_middleware
from .routers import *

__all__ = [
    "settings",
    "constants", 
    "setup_all_middleware",
    # Router exports
    "chat_router",
    "conversations_router",
    "messages_router",
    "settings_router",
    "personas_router",
    "tools_router",
    "library_router",
    "kv_router",
]