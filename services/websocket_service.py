"""
WebSocket connection manager for Ghostpad.

This module provides WebSocket connection management including:
- Connection pooling and lifecycle management
- Topic-based subscription system
- Message broadcasting to subscribed clients
- Automatic cleanup on disconnect
"""

import json
import asyncio
import logging
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection with subscription info."""
    websocket: WebSocket
    client_id: str
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=asyncio.get_event_loop().time)


class KVWebSocketManager:
    """Manages WebSocket connections for KV watching."""
    
    def __init__(self):
        # Active connections by client_id
        self.connections: Dict[str, WebSocketConnection] = {}
        # Topic subscriptions: topic -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str) -> WebSocketConnection:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            connection = WebSocketConnection(
                websocket=websocket,
                client_id=client_id
            )
            self.connections[client_id] = connection
            
        logger.info(f"WebSocket client {client_id} connected. Total connections: {len(self.connections)}")
        return connection
    
    async def disconnect(self, client_id: str):
        """Disconnect and clean up a WebSocket connection."""
        async with self._lock:
            connection = self.connections.pop(client_id, None)
            if not connection:
                return
            
            # Remove from all subscriptions
            for topic in connection.subscriptions:
                self._unsubscribe_from_topic(client_id, topic)
                
        logger.info(f"WebSocket client {client_id} disconnected. Total connections: {len(self.connections)}")
    
    async def subscribe(self, client_id: str, topic: str) -> bool:
        """Subscribe a client to a topic."""
        async with self._lock:
            connection = self.connections.get(client_id)
            if not connection:
                return False
            
            # Add to client's subscriptions
            connection.subscriptions.add(topic)
            
            # Add to topic subscriptions
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)
            
        logger.debug(f"Client {client_id} subscribed to topic '{topic}'")
        return True
    
    async def unsubscribe(self, client_id: str, topic: str) -> bool:
        """Unsubscribe a client from a topic."""
        async with self._lock:
            connection = self.connections.get(client_id)
            if not connection:
                return False
            
            self._unsubscribe_from_topic(client_id, topic)
            
        logger.debug(f"Client {client_id} unsubscribed from topic '{topic}'")
        return True
    
    def _unsubscribe_from_topic(self, client_id: str, topic: str):
        """Internal method to unsubscribe from a topic (assumes lock is held)."""
        connection = self.connections.get(client_id)
        if connection:
            connection.subscriptions.discard(topic)
        
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast a message to all clients subscribed to a topic."""
        async with self._lock:
            client_ids = self.subscriptions.get(topic, set()).copy()
        
        # Debug logging for monster HP or any key containing "monster" or "hp"
        if "monster" in topic.lower() or "hp" in topic.lower():
            print(f"🎯 Broadcasting to topic '{topic}': {len(client_ids)} subscribers")
            print(f"   Message: {message}")
            print(f"   Subscribers: {client_ids}")
        
        if not client_ids:
            if "monster" in topic.lower() or "hp" in topic.lower():
                print(f"❌ No subscribers for topic '{topic}'")
            return
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        # Send to all subscribed clients
        for client_id in client_ids:
            connection = self.connections.get(client_id)
            if not connection:
                disconnected_clients.append(client_id)
                continue
            
            try:
                await connection.websocket.send_text(message_json)
                # Debug logging for monster HP
                if "monster" in topic.lower() or "hp" in topic.lower():
                    print(f"✅ Sent {topic} update to client {client_id}")
            except Exception as e:
                logger.warning(f"Failed to send message to client {client_id}: {e}")
                if "monster" in topic.lower() or "hp" in topic.lower():
                    print(f"❌ Failed to send {topic} update to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        async with self._lock:
            client_ids = list(self.connections.keys())
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id in client_ids:
            connection = self.connections.get(client_id)
            if not connection:
                disconnected_clients.append(client_id)
                continue
            
            try:
                await connection.websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific client."""
        connection = self.connections.get(client_id)
        if not connection:
            return False
        
        try:
            message_json = json.dumps(message)
            await connection.websocket.send_text(message_json)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.connections)
    
    def get_topic_subscribers(self, topic: str) -> Set[str]:
        """Get the set of client IDs subscribed to a topic."""
        return self.subscriptions.get(topic, set()).copy()
    
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get the topics a client is subscribed to."""
        connection = self.connections.get(client_id)
        return connection.subscriptions.copy() if connection else set()


# Global instance
websocket_service = KVWebSocketManager()