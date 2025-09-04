"""
WebSocket API router for Ghostpad.

Handles WebSocket connections for real-time features including:
- KV store watching with topic subscriptions
- Bidirectional communication for subscription management
"""

import json
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from core.websocket import kv_websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/kv")
async def kv_websocket_endpoint(
    websocket: WebSocket, client_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for KV store watching with topic subscriptions."""

    logger.info(f"WebSocket connection attempt from {websocket.client}")

    # Generate client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())

    logger.info(f"Accepting WebSocket connection for client {client_id}")

    try:
        # Connect the client
        connection = await kv_websocket_manager.connect(websocket, client_id)
        logger.info(f"WebSocket connection established for client {client_id}")
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection: {e}")
        raise

    try:
        # Send welcome message with client ID
        welcome_message = {
            "type": "welcome",
            "client_id": client_id,
            "timestamp": asyncio.get_event_loop().time(),
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Message handling loop
        while True:
            try:
                logger.debug(f"Waiting for message from client {client_id}")
                # Receive message from client
                data = await websocket.receive_text()
                logger.debug(f"Received message from client {client_id}: {data}")
                message = json.loads(data)

                await handle_client_message(client_id, message)

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from client {client_id}: {e}")
                error_msg = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_msg))
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                import traceback

                traceback.print_exc()
                error_msg = {"type": "error", "message": "Internal server error"}
                try:
                    await websocket.send_text(json.dumps(error_msg))
                except:
                    logger.error(f"Failed to send error message to client {client_id}")
                    break

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        logger.info(f"Cleaning up connection for client {client_id}")
        await kv_websocket_manager.disconnect(client_id)


async def handle_client_message(client_id: str, message: Dict[str, Any]):
    """Handle incoming messages from WebSocket clients."""
    message_type = message.get("type")

    logger.info(f"📨 Received message from client {client_id}: {message_type}")

    if message_type == "subscribe":
        await handle_subscribe(client_id, message)
    elif message_type == "unsubscribe":
        await handle_unsubscribe(client_id, message)
    elif message_type == "list_subscriptions":
        await handle_list_subscriptions(client_id)
    elif message_type == "ping":
        await handle_ping(client_id, message)
    else:
        # Send error for unknown message type
        logger.warning(
            f"❓ Unknown message type from client {client_id}: {message_type}"
        )
        error_msg = {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
        }
        await kv_websocket_manager.send_to_client(client_id, error_msg)


async def handle_subscribe(client_id: str, message: Dict[str, Any]):
    """Handle subscription requests."""
    topics = message.get("topics", [])
    if isinstance(topics, str):
        topics = [topics]

    # Empty topics array means "subscribe to all"
    if not topics:
        logger.info(f"🌍 Client {client_id} subscribing to ALL KV changes")
        # Subscribe to a special "all" topic
        success = await kv_websocket_manager.subscribe(client_id, "*")
        response = {
            "type": "subscribe_response",
            "successful": ["*"] if success else [],
            "failed": [] if success else ["*"],
        }
        await kv_websocket_manager.send_to_client(client_id, response)
        return

    logger.info(f"🎯 Client {client_id} subscribing to specific topics: {topics}")

    successful_subscriptions = []
    failed_subscriptions = []

    for topic in topics:
        if isinstance(topic, str):
            success = await kv_websocket_manager.subscribe(client_id, topic)
            if success:
                successful_subscriptions.append(topic)
                logger.info(f"✅ Client {client_id} successfully subscribed to {topic}")
            else:
                failed_subscriptions.append(topic)
                logger.warning(f"❌ Client {client_id} failed to subscribe to {topic}")
        else:
            failed_subscriptions.append(str(topic))

    logger.info(
        f"📊 Client {client_id} subscription result: {len(successful_subscriptions)} successful, {len(failed_subscriptions)} failed"
    )

    # Send confirmation
    response = {
        "type": "subscribe_response",
        "successful": successful_subscriptions,
        "failed": failed_subscriptions,
    }
    await kv_websocket_manager.send_to_client(client_id, response)


async def handle_unsubscribe(client_id: str, message: Dict[str, Any]):
    """Handle unsubscription requests."""
    topics = message.get("topics", [])
    if isinstance(topics, str):
        topics = [topics]

    if not topics:
        error_msg = {
            "type": "error",
            "message": "No topics specified for unsubscription",
        }
        await kv_websocket_manager.send_to_client(client_id, error_msg)
        return

    successful_unsubscriptions = []
    failed_unsubscriptions = []

    for topic in topics:
        if isinstance(topic, str):
            success = await kv_websocket_manager.unsubscribe(client_id, topic)
            if success:
                successful_unsubscriptions.append(topic)
            else:
                failed_unsubscriptions.append(topic)
        else:
            failed_unsubscriptions.append(str(topic))

    # Send confirmation
    response = {
        "type": "unsubscribe_response",
        "successful": successful_unsubscriptions,
        "failed": failed_unsubscriptions,
    }
    await kv_websocket_manager.send_to_client(client_id, response)


async def handle_list_subscriptions(client_id: str):
    """Handle requests to list current subscriptions."""
    subscriptions = kv_websocket_manager.get_client_subscriptions(client_id)

    response = {"type": "subscriptions_list", "topics": list(subscriptions)}
    await kv_websocket_manager.send_to_client(client_id, response)


async def handle_ping(client_id: str, message: Dict[str, Any]):
    """Handle ping requests for connection health checks."""
    pong_response = {
        "type": "pong",
        "timestamp": asyncio.get_event_loop().time(),
        "original_message": message.get("data"),
    }
    await kv_websocket_manager.send_to_client(client_id, pong_response)
