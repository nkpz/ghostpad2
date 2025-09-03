from core.tool_utils import system_chunk
from db.kv_store import get_kv_store
from typing import AsyncGenerator

# KV store key for assistant mood
MOOD_KEY = "assistant_mood"

db = get_kv_store()


async def get_mood():
    """Get assistant's current mood."""
    # Initialize with default mood if none exists
    current_mood = await db.get(MOOD_KEY, None)
    if current_mood is None:
        await db.set(MOOD_KEY, "Neutral")
        return "Neutral"
    return "Current Mood: " + current_mood


async def set_mood(mood: str) -> AsyncGenerator[str, None]:
    """Set the assistant's mood with streaming text updates."""
    if not isinstance(mood, str) or not mood.strip():
        return

    # Clean and store the mood
    clean_mood = mood.strip()

    # Stream the mood change announcement
    yield system_chunk(f"🎭 The assistant is now feeling {clean_mood}\n\n")

    # Store the mood
    await db.set(MOOD_KEY, clean_mood)


TOOLS = [
    {
        "function": lambda *args, **kwargs: None,
        "report_status": get_mood,
        "auto_tool": True,
        "schema": {
            "name": "get_mood",
            "description": "Get assistant's current mood. This function provides access to the mood widget display.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "ui_feature": {
            "id": "assistant_mood_widget",
            "label": "Assistant Mood",
            "kv_key": MOOD_KEY,
            "type": "widget",
            "widget_config": {
                "type": "text",
                "format_options": {"max_length": 30, "truncate": True},
            },
        },
    },
    {
        "function": set_mood,
        "schema": {
            "name": "set_mood",
            "description": "Set the assistant's mood with streaming text updates. The mood change will be announced in real-time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood to set (should be a single word or short phrase)",
                        "maxLength": 50,
                    }
                },
                "required": ["mood"],
            },
        },
    },
]
