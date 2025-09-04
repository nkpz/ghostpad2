"""
Main FastAPI application for Ghostpad.

This module creates and configures the FastAPI application with:
- Router registration for all API endpoints
- Middleware setup (CORS, error handling, security)
- Static file serving for the frontend
- Database initialization and tool loading
- Background task management
"""

import os
import sys
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add project root to Python path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration and components
from api.config import settings, constants
from api.middleware import setup_all_middleware
from api.routers import (
    chat_router,
    conversations_router,
    messages_router,
    settings_router,
    personas_router,
    tools_router,
    library_router,
    kv_router,
    websocket_router,
)

# Import services and database components
from services.kv_store_service import kv_store
from services.tool_service import tool_service
from services.log_service import logger
from services.state_service import state_service
from services.data_access_service import data_access_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    try:
        # Initialize KV store
        logger.info("Initializing KV store...")
        await kv_store.init_db()
        
        # Initialize main database
        logger.info("Initializing database...")
        await data_access_service.initialize()
        
        # Load tools
        logger.info("Loading tools...")
        try:
            await tool_service.load_tools(settings.tools_directory)
        except Exception as e:
            logger.warning(f"Failed to load tools: {e}")
        
        # Start background condition checking task
        logger.info("Starting condition checking task...")
        condition_task = asyncio.create_task(tool_service.check_tool_conditions())
        
        # Start shared KV watcher with configured polling interval
        logger.info(f"Starting shared KV watcher (poll: {settings.kv_watcher_poll_ms}ms)...")
        state_service.start_kv_watcher(settings.kv_watcher_poll_ms)
        
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Cancel condition checking task
        if 'condition_task' in locals():
            condition_task.cancel()
        
        # Stop shared KV watcher
        logger.info("Stopping shared KV watcher...")
        try:
            await state_service.stop_kv_watcher()
        except Exception as e:
            logger.warning(f"KV watcher shutdown failed: {e}")
        
        # Run tool cleanup
        logger.info("Running tool cleanup...")
        try:
            await tool_service.cleanup_tools()
        except Exception as e:
            logger.warning(f"Tool cleanup failed: {e}")
        
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI instance with lifespan
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=settings.docs_url if settings.debug else None,
        redoc_url=settings.redoc_url if settings.debug else None,
        lifespan=lifespan
    )
    
    # Setup middleware (CORS, error handling, security, logging)
    setup_all_middleware(app)
    
    # Register API routers
    app.include_router(chat_router, tags=["chat"])
    app.include_router(conversations_router, tags=["conversations"])
    app.include_router(messages_router, tags=["messages"])
    app.include_router(settings_router, tags=["settings"])
    app.include_router(personas_router, tags=["personas"])
    app.include_router(tools_router, tags=["tools"])
    app.include_router(library_router, tags=["library"])
    app.include_router(kv_router, tags=["kv-store"])
    app.include_router(websocket_router, tags=["websocket"])
    
    # Setup static file serving
    setup_static_files(app)
    
    return app


def setup_static_files(app: FastAPI):
    """Setup static file serving for the frontend."""
    static_dir = os.path.abspath(settings.static_directory)
    
    if os.path.exists(static_dir):
        logger.info(f"Serving static files from {static_dir}")
        
        # Mount static files
        app.mount(settings.static_files_mount, StaticFiles(directory=static_dir), name="static")
        
        # Serve React app from root - this must be last to catch all unmatched routes
        @app.get("/{path:path}")
        async def serve_frontend(path: str):
            """Serve frontend files or fallback to index.html for SPA routing."""
            file_path = os.path.join(static_dir, path)
            
            # If specific file exists, serve it
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            
            # Otherwise, serve index.html (for SPA routing)
            index_path = os.path.join(static_dir, constants.FRONTEND_INDEX_FILE)
            if os.path.exists(index_path):
                return FileResponse(index_path)
            
            # Fallback if index.html doesn't exist
            return {"error": "Frontend not built or index.html missing"}
    
    else:
        logger.warning(f"Static directory not found: {static_dir}")
        
        # Provide a fallback route when frontend isn't built
        @app.get("/")
        async def api_info():
            """API information endpoint when frontend is not available."""
            return {
                "name": settings.app_name,
                "version": settings.app_version,
                "description": settings.app_description,
                "status": "running",
                "frontend": "not available - build frontend or set correct static directory",
                "docs": f"{settings.docs_url}" if settings.debug else "disabled in production",
                "api_endpoints": {
                    "chat": "/api/chat",
                    "conversations": "/api/conversations",
                    "settings": "/api/settings",
                    "tools": "/api/tools"
                }
            }


# Create the application instance
app = create_app()


# Development server entry point
if __name__ == "__main__": 
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    )