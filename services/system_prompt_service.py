"""
System prompt building service for Ghostpad.

This service handles:
- System prompt construction with datetime injection
- User description integration
- Active persona integration for conversations
- Multi-persona behavior instructions
"""

from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import select
import json

from models import ConversationPersona, Persona
from services.kv_store_service import kv_store
from services.data_access_service import with_db_session


class SystemPromptService:
    """Service for building system prompts with persona and user context."""

    @with_db_session
    async def build_system_prompt(
        self, session, conversation_id: Optional[str] = None
    ) -> str:
        """Build the system prompt with optional datetime injection and append active personas for a conversation"""
        # Get thinking mode setting and apply it at the beginning
        thinking_mode = await kv_store.get("system_prompt_thinking_mode", "default")
        thinking_prefix = ""

        if thinking_mode != "default":
            # Map the thinking mode to the appropriate string
            thinking_map = {
                "</think>": "\n\n</think>",
                "/no_think": "/no_think",
                "<no_think>": "<no_think>",
                "<think>": "<think>",
                "/think": "/think",
            }
            thinking_prefix = thinking_map.get(thinking_mode, "")

        enabled = await kv_store.get("system_prompt_enabled", True)
        if not enabled:
            base_prompt = ""
        else:
            # Get system_prompts array and join content with \n\n
            system_prompts_data = await kv_store.get("system_prompts", "[]")
            if isinstance(system_prompts_data, str):
                system_prompts = json.loads(system_prompts_data)
            else:
                system_prompts = system_prompts_data or []

            base_prompt = "\n\n".join(
                item.get("content", "") for item in system_prompts
            )

        include_datetime = await kv_store.get("system_prompt_include_datetime", False)
        if include_datetime:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            datetime_text = f"Current date and time: {current_time}"
            if base_prompt:
                base_prompt = f"{base_prompt}\n\n{datetime_text}"
            else:
                base_prompt = datetime_text

        # Add user description (the persona who uses the User role)
        user_description = await kv_store.get("user_description", "")
        user_name = await kv_store.get("user_name", "User")
        user_section = ""
        if user_description:
            user_section = f"\n\nUser's Name: {user_name}\n\nUser Description (this describes the persona that plays the 'User' role):\n{user_description}"

        # If a conversation_id is provided, append active persona descriptions
        persona_section = ""
        if conversation_id is not None:
            try:
                stmt = (
                    select(Persona)
                    .join(ConversationPersona)
                    .where(ConversationPersona.conversation_id == conversation_id)
                )
                result = await session.execute(stmt)
                personas = result.scalars().all()
                if personas:
                    # Build a descriptive block of personas
                    lines = ["Active Personas:"]
                    for p in personas:
                        desc = p.description or ""
                        lines.append(f"- {p.name}: {desc}")

                    # Behavioral instructions depending on how many personas are active
                    if len(personas) == 1:
                        p = personas[0]
                        persona_section = "\n\n" + "\n".join(lines) + "\n\n"
                        persona_section += (
                            f"Only respond as {p.name}. Use the persona description above to shape your tone, style, and content. "
                            "Do not speak as any other persona or as yourself — always reply strictly in the voice of the persona."
                        )
                    else:
                        # Multiple personas: ask model to pick and format responses explicitly
                        persona_section = "\n\n" + "\n".join(lines) + "\n\n"
                        persona_section += (
                            "Multiple active personas are available. Choose the most appropriate persona from the list above to respond to the user's request based on content, tone, and expertise. "
                            "When you reply, always begin with the persona name followed by a colon and a space, then the message, exactly in this format: `[name]: [message]`. "
                            "Do not include any additional commentary or metadata outside of that format."
                        )
            except Exception:
                # Non-fatal — just skip persona section if there's an error
                persona_section = ""

        # Combine all parts with proper spacing
        final_prompt = ""
        if thinking_prefix:
            final_prompt += thinking_prefix
            if base_prompt or user_section or persona_section:
                final_prompt += "\n\n"

        final_prompt += (base_prompt or "") + user_section + persona_section
        return final_prompt

    async def get_system_prompt_settings(self) -> dict:
        """Get current system prompt settings."""
        system_prompts_data = await kv_store.get("system_prompts", "[]")
        if isinstance(system_prompts_data, str):
            system_prompts = json.loads(system_prompts_data)
        else:
            system_prompts = system_prompts_data or []

        return {
            "system_prompts": system_prompts,
            "include_datetime": await kv_store.get(
                "system_prompt_include_datetime", False
            ),
            "enabled": await kv_store.get("system_prompt_enabled", True),
            "thinking_mode": await kv_store.get(
                "system_prompt_thinking_mode", "default"
            ),
        }

    async def save_system_prompt_settings(
        self,
        system_prompts: List[Any],
        include_datetime: bool,
        enabled: bool,
        thinking_mode: str = "default",
    ) -> dict:
        """Save system prompt settings."""
        # Convert list of SystemPromptItem Pydantic objects to JSON-serializable format
        prompts_data = [
            {"title": item.title, "content": item.content} for item in system_prompts
        ]
        await kv_store.set("system_prompts", json.dumps(prompts_data))
        await kv_store.set("system_prompt_include_datetime", include_datetime)
        await kv_store.set("system_prompt_enabled", enabled)
        await kv_store.set("system_prompt_thinking_mode", thinking_mode)

        return {
            "system_prompts": prompts_data,
            "include_datetime": include_datetime,
            "enabled": enabled,
            "thinking_mode": thinking_mode,
        }

    async def get_user_description_settings(self) -> dict:
        """Get user description settings."""
        return {
            "user_description": await kv_store.get("user_description", ""),
            "user_name": await kv_store.get("user_name", "User"),
        }

    async def save_user_description_settings(
        self, user_description: str, user_name: str = "User"
    ) -> dict:
        """Save user description settings."""
        await kv_store.set("user_description", user_description or "")
        await ("user_name", user_name or "User")
        return {
            "user_description": user_description or "",
            "user_name": user_name or "User",
        }


# Global system prompt service instance
system_prompt_service = SystemPromptService()
