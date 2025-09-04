"""
Server-Sent Events (SSE) service for Ghostpad.

This service handles the conversion of internal service events to SSE format,
providing a centralized way to format streaming responses for web clients.
"""

import json
from typing import Dict, Any, AsyncGenerator


class SSEService:
    """Service for handling Server-Sent Events formatting."""
    
    @staticmethod
    def get_sse_headers() -> Dict[str, str]:
        """Get standard headers for Server-Sent Events streaming."""
        return {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }

    def convert_event_to_sse(self, event: Dict[str, Any]) -> str:
        """Convert a service event to SSE format.
        
        Args:
            event: Event dictionary from service layer
            
        Returns:
            SSE-formatted string ready for streaming
        """
        event_type = event.get("type")
        
        # Handle different event types with appropriate SSE formatting
        if event_type == "start":
            return f"data: {json.dumps({'type': 'stream_start'})}\n\n"
            
        elif event_type == "chunk":
            content = event.get('content', '')
            return f"data: {json.dumps({'type': 'stream_chunk', 'content': content})}\n\n"
            
        elif event_type == "system_chunk":
            content = event.get('content', '')
            return f"data: {json.dumps({'type': 'system_chunk', 'content': content})}\n\n"
            
        elif event_type == "system_complete":
            message_data = event.get("message", {})
            return f"data: {json.dumps({'type': 'system_complete', 'message': message_data})}\n\n"
            
        elif event_type == "message_complete":
            message_data = event.get("message", {})
            return f"data: {json.dumps({'type': 'message_complete', 'message': message_data})}\n\n"
            
        elif event_type == "complete":
            content = event.get('content', '')
            return f"data: {json.dumps({'type': 'complete', 'content': content})}\n\n"
            
        elif event_type == "error":
            err_msg = event.get('message', '')
            return f"data: {json.dumps({'error': err_msg})}\n\n"
            
        else:
            # Unknown event type, pass through with minimal formatting
            return f"data: {json.dumps(event)}\n\n"

    async def stream_service_events(
        self, 
        events: AsyncGenerator[Dict[str, Any], None], 
        error_prefix: str = "Error"
    ) -> AsyncGenerator[str, None]:
        """Convert a stream of service events to SSE format.
        
        Args:
            events: Async generator of service events
            error_prefix: Prefix for error messages
            
        Yields:
            SSE-formatted strings
        """
        try:
            async for event in events:
                yield self.convert_event_to_sse(event)
        except Exception as e:
            error_event = {"error": f"{error_prefix}: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"

    def format_custom_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format a custom event for SSE streaming.
        
        Args:
            event_type: Type of the event (e.g., 'user_message', 'notification')
            data: Event data dictionary
            
        Returns:
            SSE-formatted string
        """
        event_data = {"type": event_type, **data}
        return f"data: {json.dumps(event_data)}\n\n"


# Global service instance
sse_service = SSEService()