"""
API routers package for Ghostpad.

This package provides FastAPI routers for all endpoints:
- Chat message handling and streaming
- Conversation management
- Message operations
- Settings configuration
- Persona management
- Tool management
- Library snippet operations
- Key-Value store operations
"""

from .chat import router as chat_router
from .conversations import router as conversations_router
from .messages import router as messages_router
from .settings import router as settings_router
from .personas import router as personas_router
from .tools import router as tools_router
from .library import router as library_router
from .kv import router as kv_router
from .websocket import router as websocket_router

__all__ = [
    "chat_router",
    "conversations_router", 
    "messages_router",
    "settings_router",
    "personas_router",
    "tools_router",
    "library_router",
    "kv_router",
    "websocket_router",
]