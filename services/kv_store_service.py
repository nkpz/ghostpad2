from contextlib import asynccontextmanager
import json
import os
from typing import Any, List, Union

import aiosqlite


class KVStoreService:
    """
    A lightweight async SQLite wrapper with Redis-like interface.
    Supports strings and lists with automatic serialization.
    Compatible with database clients like DBeaver.
    """

    def __init__(self, db_path: str = "data.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    async def init_db(self):
        """Initialize the database schema"""
        async with self._get_connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await conn.commit()

    @asynccontextmanager
    async def _get_connection(self):
        """Async context manager for database connections"""
        conn = await aiosqlite.connect(self.db_path)
        try:
            yield conn
        finally:
            await conn.close()

    def _serialize(self, value: Any) -> tuple[str, str]:
        """Serialize Python objects to JSON string and return type info"""
        data_type = type(value).__name__
        json_value = json.dumps(value)
        return json_value, data_type

    def _deserialize(self, json_value: str) -> Any:
        """Deserialize JSON string back to Python objects"""
        try:
            return json.loads(json_value)
        except (json.JSONDecodeError, TypeError):
            return json_value

    # String operations
    async def set(self, key: str, value: Union[str, int, float]) -> None:
        """Set a string value"""
        json_value, data_type = self._serialize(value)
        async with self._get_connection() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO kv_store (key, value, data_type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (key, json_value, data_type),
            )
            await conn.commit()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a string value"""
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT value, data_type FROM kv_store WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            if row:
                json_value, _ = row
                return self._deserialize(json_value)
            return default

    async def delete(self, key: str) -> bool:
        """Delete a key"""
        async with self._get_connection() as conn:
            cursor = await conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            await conn.commit()
            return cursor.rowcount > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._get_connection() as conn:
            cursor = await conn.execute("SELECT 1 FROM kv_store WHERE key = ?", (key,))
            return await cursor.fetchone() is not None

    # List operations
    async def lpush(self, key: str, *values) -> int:
        """Push values to the left of a list"""
        current = await self.get(key, [])
        if not isinstance(current, list):
            current = []

        for value in reversed(values):
            current.insert(0, value)

        await self.set(key, current)
        return len(current)

    async def rpush(self, key: str, *values) -> int:
        """Push values to the right of a list"""
        current = await self.get(key, [])
        if not isinstance(current, list):
            current = []

        current.extend(values)
        await self.set(key, current)
        return len(current)

    async def lpop(self, key: str) -> Any:
        """Pop value from the left of a list"""
        current = await self.get(key, [])
        if not isinstance(current, list) or not current:
            return None

        value = current.pop(0)
        await self.set(key, current)
        return value

    async def rpop(self, key: str) -> Any:
        """Pop value from the right of a list"""
        current = await self.get(key, [])
        if not isinstance(current, list) or not current:
            return None

        value = current.pop()
        await self.set(key, current)
        return value

    async def llen(self, key: str) -> int:
        """Get length of a list"""
        current = await self.get(key, [])
        if not isinstance(current, list):
            return 0
        return len(current)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get a range of elements from a list"""
        current = await self.get(key, [])
        if not isinstance(current, list):
            return []

        if end == -1:
            return current[start:]
        return current[start : end + 1]

    async def lremove_at(self, key: str, index: int) -> bool:
        """Remove item at specific index from a list"""
        current = await self.get(key, [])
        if not isinstance(current, list) or index >= len(current) or index < 0:
            return False

        current.pop(index)
        await self.set(key, current)
        return True

    # Utility methods
    async def keys(self) -> List[str]:
        """Get all keys"""
        async with self._get_connection() as conn:
            cursor = await conn.execute("SELECT key FROM kv_store")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def clear(self) -> None:
        """Clear all data"""
        async with self._get_connection() as conn:
            await conn.execute("DELETE FROM kv_store")
            await conn.commit()

    async def delete_keys_containing(self, pattern: str) -> int:
        """Delete all keys that contain the given pattern"""
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM kv_store WHERE key LIKE ?", (f"%{pattern}%",)
            )
            await conn.commit()
            return cursor.rowcount


kv_store = KVStoreService("data.db")
