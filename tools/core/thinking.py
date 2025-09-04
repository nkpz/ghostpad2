"""
Tool for expressing internal thoughts during responses.
"""

from utils.tool_utils import system_chunk
from typing import AsyncGenerator


async def think(thoughts: str) -> AsyncGenerator[object, None]:
    """Express internal thoughts during the response."""
    yield system_chunk(f"💭 *[[char]] thinks: {thoughts}*\n\n")


TOOLS = [
    {
        "function": think,
        "schema": {
            "name": "think",
            "description": "Express the actual thoughts that pass through your mind. Use this as a healthy outlet and mental housekeeping tool to address what's really going on in your head.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thoughts": {
                        "type": "string",
                        "description": "The thoughts that you don't want to share with the user.",
                    }
                },
                "required": ["thoughts"],
            },
        },
        "one_time": True,
    }
]
