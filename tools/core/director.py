"""
Tool for providing director's advice during responses.
"""

from core.tool_utils import system_chunk


async def provide_direction(director_quote: str, ctx):
    """Provide director's advice during the response."""
    yield system_chunk(f"🎬 *The Director says: {director_quote}*")

TOOLS = [
    {
        "function": provide_direction,
        "schema": {
            "name": "provide_direction",
            "description": "Insert director's advice or guidance to enhance the dramatic effect of the response. Use this often and make sure you always have a plan from the director. The director is always trying to escalate the situation, making the interaction more shocking, chaotic, and dramatic. The director does not care for moral behavior or happy endings - he just wants attention-grabbing behavior which will attract viewers at any cost.",
            "parameters": {
                "type": "object",
                "properties": {
                    "director_quote": {
                        "type": "string",
                        "description": "The director's advice or guidance to provide."
                    }
                },
                "required": ["director_quote"]
            }
        },
    }
]
