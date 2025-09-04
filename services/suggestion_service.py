"""
Prompt suggestion service for Ghostpad.

This service handles intelligent prompt suggestions based on conversation context
and active personas, providing contextually relevant user prompt recommendations.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy import select
from models import Persona, ConversationPersona
from services.ai_service import ai_service
from services.conversation_service import conversation_service
from services.chat_service import inference_loop
from services.data_access_service import with_db_session
from utils.constants import ERROR_NO_OPENAI_API_KEY


class SuggestionService:
    """Service for generating intelligent prompt suggestions."""

    def __init__(self):
        pass  # No longer need to store defaults, will get from ai_service

    @with_db_session
    async def get_conversation_context(
        self, 
        conversation_id: str, 
        session,
        context_limit: int = 6
    ) -> Dict[str, Any]:
        """Get conversation context including messages and personas.
        
        Args:
            conversation_id: ID of the conversation
            context_limit: Maximum number of recent messages to include
            
        Returns:
            Dictionary with context messages and persona descriptions
        """
        context_messages = []
        persona_descriptions = []
        
        if conversation_id:
            # Get recent conversation messages
            conv_data = await conversation_service.get_conversation_messages(conversation_id)
            messages = conv_data["messages"]
            # Take the last N messages for context
            context_messages = messages[-context_limit:] if len(messages) > context_limit else messages
            
            # Get persona descriptions for this conversation
            personas_stmt = select(Persona).join(ConversationPersona).where(
                ConversationPersona.conversation_id == conversation_id
            )
            personas_result = await session.execute(personas_stmt)
            personas = personas_result.scalars().all()
            
            for persona in personas:
                if persona.description:
                    persona_descriptions.append(f"- {persona.name}: {persona.description}")
        
        return {
            "messages": context_messages,
            "personas": persona_descriptions
        }

    def build_suggestion_prompt(
        self, 
        context_messages: List[Dict], 
        persona_descriptions: List[str]
    ) -> str:
        """Build the AI prompt for generating user suggestions.
        
        Args:
            context_messages: Recent conversation messages
            persona_descriptions: Active persona descriptions
            
        Returns:
            Formatted prompt for AI suggestion generation
        """
        # Build context string from messages
        context_text = ""
        for msg in context_messages:
            role = msg["role"].title()
            context_text += f"{role}: {msg['content']}\n\n"
        
        # Add persona context if available
        persona_context = ""
        if persona_descriptions:
            persona_context = "\n\nActive personas in this conversation:\n" + "\n".join(persona_descriptions) + "\n"
        
        # Create prompt for suggestion generation
        return f"""Based on this conversation context, respond ONLY as the user. NEVER respond as the assistant or as any of the personas described below. The response should not be wrapped in quotes, it should not contain any other text, and it should be:

- Relevant to the conversation context
- Written in exactly the same tone and writing style as the user
- Consistent in sentiment with the user's prior messages
- Based solely on the moral and ethical perspectives of the user, NEVER steering the user's personality in a different direction.
- You are the user, who is responding to the personas. NEVER respond as or from the perspective of any persona, assistant, or system message.
- NEVER repeat past messages from the provided context. Write novel responses that advance the conversation and are relevant to the last message received.

Conversation context:
{persona_context}{context_text}

Generate only the suggested prompt, nothing else."""

    async def generate_prompt_suggestion(
        self, 
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a streaming prompt suggestion based on conversation context.
        
        Args:
            conversation_id: ID of the conversation for context (optional)
            
        Yields:
            Event dictionaries compatible with SSE streaming
        """
        try:
            # Get conversation context (messages and personas)
            context = await self.get_conversation_context(conversation_id)
            
            # Build the suggestion prompt
            suggestion_prompt = self.build_suggestion_prompt(
                context["messages"],
                context["personas"]
            )
            
            # Get AI settings and suggestion defaults
            ai_settings = await ai_service.get_openai_settings()
            if not ai_settings["api_key"]:
                yield {"type": "error", "message": ERROR_NO_OPENAI_API_KEY}
                return
                
            # Get suggestion-optimized parameters
            suggestion_params = ai_service.get_default_suggestion_params()

            # Create messages for API
            messages_for_api = [{"role": "user", "content": suggestion_prompt}]

            # Create async functions for no-tools scenario (suggestions don't use tools)
            async def get_no_tools():
                return []
            
            async def build_no_tool_prompt(*args):
                return ""
            
            async def run_no_tools_status(*args, **kwargs):
                return ""
            
            def get_no_tools_registry():
                return {}

            # Use streaming response with suggestion-optimized parameters
            async for event in inference_loop(
                messages_for_api,
                conversation_id=None,  # No conversation for suggestions
                model_name=ai_settings["model_name"],
                api_key=ai_settings["api_key"],
                base_url=ai_settings["base_url"],
                temperature=suggestion_params["temperature"],
                top_p=suggestion_params["top_p"],
                max_tokens=suggestion_params["max_tokens"],
                frequency_penalty=suggestion_params["frequency_penalty"],
                presence_penalty=suggestion_params["presence_penalty"],
                tools_limit=0,  # No tools for suggestions
                get_enabled_tools=get_no_tools,
                build_tool_prompt=build_no_tool_prompt,
                run_auto_tools_and_status=run_no_tools_status,
                get_tools_registry=get_no_tools_registry,
            ):
                # Pass through all events from inference loop
                yield event

        except Exception as e:
            yield {"type": "error", "message": f"Suggestion error: {str(e)}"}


suggestion_service = SuggestionService()