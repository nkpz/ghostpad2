"""
Application configuration for Ghostpad.

This module provides configuration management for the FastAPI application
including environment variables, default settings, and application constants.
"""

import os
from typing import List, Optional
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings configuration."""
    
    # Application Info
    app_name: str = "Ghostpad"
    app_description: str = "Modular frontend for OpenAI API compatible servers with expanded tool API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database Configuration
    conversations_db_url: str = "sqlite+aiosqlite:///conversations.db"
    kv_store_db_path: str = "data.db"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]  # In production, should be more restrictive
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Static Files
    static_directory: str = "frontend/dist"
    static_files_mount: str = "/static"
    
    # Tools Configuration
    tools_directory: str = "tools"
    tools_limit: int = 3  # Default tools limit per response
    
    # KV Watcher Configuration
    kv_watcher_poll_ms: int = 1000  # Default polling interval in milliseconds
    
    # API Configuration
    api_prefix: str = "/api"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Security
    allowed_hosts: List[str] = ["*"]  # In production, should be more restrictive
    
    # Logging
    log_level: str = "INFO"
    
    # Performance
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    request_timeout: int = 300  # 5 minutes
    
    class Config:
        """Pydantic config for environment variable loading."""
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings with environment variable overrides."""
    return Settings(
        # Override with environment variables
        debug=os.getenv("DEBUG", "false").lower() == "true",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        conversations_db_url=os.getenv("CONVERSATIONS_DB_URL", "sqlite+aiosqlite:///conversations.db"),
        kv_store_db_path=os.getenv("KV_STORE_DB_PATH", "data.db"),
        static_directory=os.getenv("STATIC_DIRECTORY", "frontend/dist"),
        tools_directory=os.getenv("TOOLS_DIRECTORY", "tools"),
        tools_limit=int(os.getenv("TOOLS_LIMIT", "3")),
        kv_watcher_poll_ms=int(os.getenv("KV_WATCHER_POLL_MS", "1000")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"],
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",") if os.getenv("ALLOWED_HOSTS") else ["*"],
    )


# Global settings instance
settings = get_settings()


class AppConstants:
    """Application constants and default values."""
    
    # Default persona info
    DEFAULT_PERSONA_NAME = "Assistant"
    DEFAULT_PERSONA_DESCRIPTION = "Default assistant persona"
    
    # Tool execution constants
    MAX_TOOL_EXECUTION_TIME = 60  # seconds
    DEFAULT_TOOL_TIMEOUT = 30  # seconds
    
    # Chat constants
    MAX_MESSAGE_LENGTH = 50000  # characters
    MAX_CONVERSATION_TITLE_LENGTH = 255  # characters
    
    # Streaming constants
    STREAM_CHUNK_SIZE = 1024
    
    # File paths
    FRONTEND_INDEX_FILE = "index.html"


# Export commonly used values
constants = AppConstants()