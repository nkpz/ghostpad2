"""
Shared application state service for Ghostpad.

This service maintains global state that needs to be shared across different
parts of the application, particularly for SSE event subscriptions and KV watching.
"""

import asyncio
import aiosqlite
from typing import List, Dict, Optional
from .websocket_service import websocket_service
from .kv_store_service import kv_store


class StateService:
    """Service for managing shared application state."""

    def __init__(self):
        # Condition results cache for tracking changes
        self.condition_results_cache: Dict[str, bool] = {}
        
        # KV Watcher system
        self.kv_watcher_task: Optional[asyncio.Task] = None
        self.kv_watcher_running: bool = False

    def start_kv_watcher(self, poll_ms: int = 1000):
        """Start the shared KV watcher if not already running."""
        if self.kv_watcher_running:
            return
        
        self.kv_watcher_running = True
        self.kv_watcher_task = asyncio.create_task(self._kv_watcher_loop(poll_ms))

    async def stop_kv_watcher(self):
        """Stop the shared KV watcher."""
        if self.kv_watcher_task and not self.kv_watcher_task.done():
            self.kv_watcher_task.cancel()
            await self.kv_watcher_task
        
        self.kv_watcher_running = False
        self.kv_watcher_task = None

    async def _kv_watcher_loop(self, poll_ms: int):
        """Internal shared KV watcher loop."""
        
        db_path = getattr(kv_store, "db_path", "data.db")
        last_updated: Dict[str, str | None] = {}
        
        while True:
            try:
                # Check if we have any WebSocket subscribers
                if websocket_service.get_connection_count() == 0:
                    # No subscribers, sleep longer
                    await asyncio.sleep(max(1.0, poll_ms / 1000))
                    continue
                    
                async with aiosqlite.connect(db_path) as conn:
                    # Get all keys and their updated_at timestamps
                    cursor = await conn.execute("SELECT key, updated_at FROM kv_store")
                    rows = await cursor.fetchall()
                    
                    for key, updated_at in rows:
                        if last_updated.get(key) != updated_at:
                            last_updated[key] = updated_at
                            
                            # Get the actual value
                            try:
                                current_value = await kv_store.get(key, None)
                                current_len = await kv_store.llen(key) if isinstance(current_value, list) else 0
                            except Exception:
                                current_value = None
                                current_len = 0
                            
                            payload = {"type": "kv_update", "key": key, "value": current_value, "len": current_len}
                            
                            # Broadcast to WebSocket subscribers
                            try:
                                # Only broadcast to "all" subscribers (simplified approach)
                                await websocket_service.broadcast_to_topic("*", payload)
                            except Exception as e:
                                print(f"Error broadcasting to WebSocket subscribers: {e}")
                
                await asyncio.sleep(max(0.05, poll_ms / 1000))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error and continue
                print(f"Error in KV watcher loop: {e}")
                await asyncio.sleep(1.0)


# Global service instance
state_service = StateService()