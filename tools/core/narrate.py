"""
Tool for providing story narration.
"""

from core.tool_utils import system_chunk


async def narrate(narration_text: str):
    """Provide director's advice during the response."""
    yield system_chunk(f"[NARRATOR]\n\n{narration_text}*")


TOOLS = [
    {
        "function": narrate,
        "one_time": True,
        "schema": {
            "name": "narrate",
            "description": "Insert narration to enrich the storytelling, emphasizing high-quality writing that advances the plot in clever, surprising, or emotionally engaging ways. The narration should avoid flat exposition and instead weave in tone, atmosphere, and subtle foreshadowing to keep the reader invested. Use descriptive writing to communicate the sights, sounds, smells, and feelings that the characters are experiencing. Always end the narration wiht a list of **key insights**.",
            "parameters": {
                "type": "object",
                "properties": {
                    "narration_text": {
                        "type": "string",
                        "description": "Narrative prose that enhances the scene by advancing the story, meticulously describing the atmosphere, or revealing character depth in an artful way. At the end of the narration, add a list of key insights, which are observations in the scene that may help the user advance the plot further.",
                    }
                },
                "required": ["narration_text"],
            },
        },
    }
]
