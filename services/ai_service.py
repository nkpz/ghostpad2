"""
AI service for OpenAI integration.

This service handles:
- OpenAI API configuration and settings
- Connection testing and model listing
- Sampling parameter management
- Client creation and management
"""

from typing import Dict, Any
from openai import OpenAI
from services.kv_store_service import kv_store
from utils.constants import ERROR_NO_OPENAI_API_KEY


class AIService:
    """Service for managing OpenAI API integration."""

    async def get_openai_settings(self) -> Dict[str, Any]:
        """Get OpenAI API settings."""
        return {
            "base_url": await kv_store.get(
                "openai_base_url", "https://api.openai.com/v1"
            ),
            "api_key": await kv_store.get("openai_api_key", ""),
            "model_name": await kv_store.get("openai_model_name", "gpt-3.5-turbo"),
            "streaming_enabled": await kv_store.get("openai_streaming_enabled", True),
        }

    async def save_openai_settings(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        streaming_enabled: bool = True,
    ) -> Dict[str, Any]:
        """Save OpenAI API settings."""
        await kv_store.set("openai_base_url", base_url)
        await kv_store.set("openai_api_key", api_key)
        await kv_store.set("openai_model_name", model_name)
        await kv_store.set("openai_streaming_enabled", streaming_enabled)

        return {
            "base_url": base_url,
            "api_key": api_key,
            "model_name": model_name,
            "streaming_enabled": streaming_enabled,
        }

    def test_connection(self, base_url: str, api_key: str) -> Dict[str, Any]:
        """Test connection to OpenAI API and return available models."""
        try:
            # Create OpenAI client with provided settings
            client = OpenAI(api_key=api_key, base_url=base_url)

            # Test connection by listing available models
            models_response = client.models.list()

            # Extract model names and info
            models = []
            for model in models_response.data:
                models.append(
                    {
                        "id": model.id,
                        "created": getattr(model, "created", None),
                        "owned_by": getattr(model, "owned_by", "unknown"),
                    }
                )

            # Sort models by name for better UX
            models.sort(key=lambda x: x["id"])

            return {
                "success": True,
                "message": f"Connection successful! Found {len(models)} available models.",
                "model_info": {"models": models},
            }

        except Exception as e:
            error_message = str(e)

            # Provide more specific error messages
            if "401" in error_message or "authentication" in error_message.lower():
                message = "Authentication failed. Please check your API key."
            elif "404" in error_message or "not found" in error_message.lower():
                message = "Endpoint not found. Please check your base URL."
            elif "timeout" in error_message.lower():
                message = "Connection timeout. Please check your base URL and network connection."
            elif "connection" in error_message.lower():
                message = "Unable to connect to the API. Please check your base URL."
            else:
                message = f"Connection failed: {error_message}"

            return {"success": False, "message": message}

    async def get_sampling_settings(self) -> Dict[str, Any]:
        """Get sampling parameters."""
        settings = {
            "temperature": await kv_store.get("sampling_temperature", 1.0),
            "top_p": await kv_store.get("sampling_top_p", 1.0),
            "max_tokens": await kv_store.get("sampling_max_tokens", 1000),
            "frequency_penalty": await kv_store.get("sampling_frequency_penalty", 0.0),
            "presence_penalty": await kv_store.get("sampling_presence_penalty", 0.0),
        }

        # Add optional parameters if they exist
        seed = await kv_store.get("sampling_seed", None)
        if seed is not None:
            settings["seed"] = seed

        return settings

    async def save_sampling_settings(
        self,
        temperature: float,
        top_p: float,
        max_tokens: int,
        frequency_penalty: float,
        presence_penalty: float,
        seed: int = None,
    ) -> Dict[str, Any]:
        """Save sampling parameters."""
        await kv_store.set("sampling_temperature", temperature)
        await kv_store.set("sampling_top_p", top_p)
        await kv_store.set("sampling_max_tokens", max_tokens)
        await kv_store.set("sampling_frequency_penalty", frequency_penalty)
        await kv_store.set("sampling_presence_penalty", presence_penalty)

        # Save optional parameters
        if seed is not None:
            await kv_store.set("sampling_seed", seed)
        else:
            await kv_store.delete("sampling_seed")

        result = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }

        # Add optional parameters to result if they were provided
        if seed is not None:
            result["seed"] = seed

        return result

    async def create_client(self) -> OpenAI:
        """Create an OpenAI client with current settings."""
        settings = await self.get_openai_settings()
        return OpenAI(api_key=settings["api_key"], base_url=settings["base_url"])

    async def edit_prompt(self, draft: str, instructions: str) -> str:
        """Edit a prompt using the configured OpenAI model."""
        settings = await self.get_openai_settings()

        if not settings["api_key"]:
            raise ValueError(ERROR_NO_OPENAI_API_KEY)

        try:
            client = OpenAI(api_key=settings["api_key"], base_url=settings["base_url"])

            sys_prompt = (
                "You are an expert editor. You will receive a draft text and editing instructions. "
                "Return ONLY the fully edited text, without explanations, metadata, or code fences."
            )
            user_prompt = (
                f"Instructions:\n{instructions}\n\n---\nDraft:\n{draft}\n---\n"
            )

            resp = client.chat.completions.create(
                model=settings["model_name"],
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                top_p=0.9,
            )

            return (resp.choices[0].message.content or "").strip()

        except Exception as e:
            raise Exception(f"Edit failed: {str(e)}")

    async def generate_title(self, user_message: str, assistant_message: str) -> str:
        """Generate a conversation title based on the first exchange."""
        settings = await self.get_openai_settings()

        if not settings["api_key"]:
            raise ValueError(ERROR_NO_OPENAI_API_KEY)

        try:
            # Create a focused prompt for title generation
            title_prompt = f"""Based on this conversation, generate a concise, descriptive title (3-6 words maximum):

User: {user_message}
Assistant: {assistant_message}

Generate only the title, nothing else. Make it specific and informative. You must STOP thinking about your response and respond immediately."""

            # Call OpenAI API for title generation - but keep it focused for titles!
            client = OpenAI(api_key=settings["api_key"], base_url=settings["base_url"])

            response = client.chat.completions.create(
                model=settings["model_name"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates concise, descriptive conversation titles without any prior reasoning or thinking. Respond with only the title, no quotes or additional text.\n\n"
                        + title_prompt,
                    },
                ],
                max_tokens=1000,
                reasoning_effort="low",
                temperature=0.7,  # Keep titles consistent, not too wild!
                top_p=0.9,
            )
            print("Title generation called", response)

            generated_title = response.choices[0].message.content.strip()
            # Clean up the title (remove surrounding single or double quotes if present)
            generated_title = generated_title.strip("\"'")[:50]

            return generated_title

        except Exception as e:
            # If title generation fails, return a default title
            print(f"Title generation failed: {str(e)}")
            return "New Chat"

    def get_default_suggestion_params(self) -> Dict[str, Any]:
        """Get default AI parameters optimized for prompt suggestions.

        Returns:
            Dictionary with suggestion-optimized AI parameters
        """
        return {
            "temperature": 0.7,  # Slightly creative
            "top_p": 0.97,
            "max_tokens": 100,  # Short suggestions
            "frequency_penalty": 0.2,
            "presence_penalty": 0.2,
        }

    def get_default_chat_params(self) -> Dict[str, Any]:
        """Get default AI parameters for regular chat.

        Returns:
            Dictionary with chat-optimized AI parameters
        """
        return {
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 1000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }


# Global AI service instance
ai_service = AIService()
