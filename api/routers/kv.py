"""
Key-Value Store API router for Ghostpad.

Handles KV store operations including scalar get/set and list operations.
The KV store is a layer on top of SQLite. See db/kv_store.py
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any

from services.kv_store_service import kv_store
from services.chat_service import replace_message_placeholders

router = APIRouter()

# Pydantic models
class KVSetRequest(BaseModel):
    key: str
    value: Any = None

class KVListRemoveItemRequest(BaseModel):
    key: str
    index: int

class KVRPushRequest(BaseModel):
    key: str
    value: Any

class KVClearRequest(BaseModel):
    key: str


@router.get("/api/kv/get")
async def kv_get(key: str = None, keys: str = None, conversation_id: str = None):
    """Get scalar value(s) from kv_store. Use 'key' for single value or 'keys' for comma-separated list.
    If conversation_id is provided, string values will have placeholders replaced."""
    try:
        if keys:
            # Batch get multiple keys
            key_list = [k.strip() for k in keys.split(',') if k.strip()]
            result = {}
            for k in key_list:
                value = await kv_store.get(k, None)
                # Apply placeholder replacement if conversation_id provided and value is string
                if conversation_id and isinstance(value, str):
                    value = await replace_message_placeholders(value, conversation_id)
                result[k] = value
            return {"keys": result}
        elif key:
            # Single key get
            value = await kv_store.get(key, None)
            # Apply placeholder replacement if conversation_id provided and value is string
            if conversation_id and isinstance(value, str):
                value = await replace_message_placeholders(value, conversation_id)
            return {"key": key, "value": value}
        else:
            raise HTTPException(status_code=400, detail="Must provide either 'key' or 'keys' parameter")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/kv/set")
async def kv_set(data: KVSetRequest):
    """Set a scalar value in kv_store."""
    try:
        await kv_store.set(data.key, data.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/kv/list/len")
async def kv_list_len(key: str):
    """Return the length of a list-like key (0 if not a list or missing)."""
    try:
        length = await kv_store.llen(key)
    except Exception:
        length = 0
    return {"key": key, "len": length}


@router.get("/api/kv/list")
async def kv_list(key: str, start: int = Query(-50), end: int = Query(-1), conversation_id: str = None):
    """Return a slice of a list-like key. If conversation_id is provided, string items will have placeholders replaced."""
    try:
        items = await kv_store.lrange(key, start, end)
        # Apply placeholder replacement if conversation_id provided
        if conversation_id and items:
            processed_items = []
            for item in items:
                if isinstance(item, str):
                    item = await replace_message_placeholders(item, conversation_id)
                processed_items.append(item)
            items = processed_items
    except Exception:
        items = []
    return {"key": key, "items": items, "start": start, "end": end}


@router.post("/api/kv/list/rpush")
async def kv_list_rpush(data: KVRPushRequest):
    """Append a value to the right of a list-like key."""
    try:
        await kv_store.rpush(data.key, data.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/kv/list/remove-item")
async def kv_list_remove_item(data: KVListRemoveItemRequest):
    """Remove item at specific index from a list."""
    try:
        success = await kv_store.lremove_at(data.key, data.index)
        return {"ok": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/kv/list/clear")
async def kv_list_clear(data: KVClearRequest):
    """Clear a list-like key entirely."""
    try:
        await kv_store.set(data.key, [])
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


