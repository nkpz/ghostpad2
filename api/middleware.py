"""
Middleware configuration for Ghostpad.

This module provides middleware setup for the FastAPI application including
CORS handling, error processing, logging, and security features.
"""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from services.log_service import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling and formatting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
        except ValueError as e:
            # Convert ValueError to 400 Bad Request
            return JSONResponse(
                status_code=400,
                content={"detail": str(e), "type": "validation_error"}
            )
        except Exception as e:
            # Convert unexpected errors to 500 Internal Server Error
            logger.exception(f"Unexpected error processing request: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error occurred",
                    "type": "internal_error",
                    # In debug mode, include the actual error message
                    **({"debug_message": str(e)} if settings.debug else {})
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add CSP header for better security (can be customized based on needs)
        if not settings.debug:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'"
            )
        
        return response


def setup_cors_middleware(app):
    """Configure CORS middleware for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
        expose_headers=["X-Process-Time"]  # Expose timing header
    )


def setup_trusted_host_middleware(app):
    """Configure trusted host middleware for the application."""
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )


def setup_custom_middleware(app):
    """Add custom middleware to the application."""
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add logging middleware (should be last for accurate timing)
    if settings.debug:
        app.add_middleware(LoggingMiddleware)


def setup_all_middleware(app):
    """Setup all middleware for the application in correct order."""
    
    # Order matters! Middleware is applied in reverse order of addition
    # (first added = outermost = last to process request, first to process response)
    
    # 1. CORS (outermost)
    setup_cors_middleware(app)
    
    # 2. Trusted Host
    setup_trusted_host_middleware(app)
    
    # 3. Custom middleware (innermost)
    setup_custom_middleware(app)