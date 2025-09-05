"""
Chat service for message handling and chat logic.

This service handles:
- Message processing and persistence
- Chat response generation
- Message editing and deletion
- Conversation history management
- AI inference and streaming
"""

"""
Chat service for message handling and chat logic.

This service handles:
- Message processing and persistence
- Chat response generation
- Message editing and deletion
- Conversation history management
- AI inference and streaming
"""

from services.data_access_service import with_db_session
from utils.constants import ERROR_MESSAGE_NOT_FOUND, ERROR_MESSAGE_NOT_FOUND_REGEN, ERROR_NO_OPENAI_API_KEY
from .tool_service import tool_service
from .persona_service import persona_service
from .system_prompt_service import system_prompt_service
from .ai_service import ai_service
from .kv_store_service import kv_store
from models import Conversation, Message, MessageAttachment
from utils.response_context import ResponseContext
from openai import AsyncOpenAI
from sqlalchemy import select, func
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import inspect
import asyncio
import json


async def replace_message_placeholders(content: str, conversation_id: str) -> str:
    """Replace {{user}} and {{char}} placeholders in message content."""
    try:
        user_name = await kv_store.get("user_name", "User")

        persona_names = await persona_service.get_persona_names_for_conversation(
            conversation_id
        )
        char_name = persona_names[0] if persona_names else "Assistant"

        processed_content = (
            content.replace("{{user}}", user_name)
            .replace("{{char}}", char_name)
            .replace("[[user]]", user_name)
            .replace("[[char]]", char_name)
        )

        return processed_content
    except Exception as e:
        print(f"[DEBUG] Error replacing placeholders: {e}")
        return content  # Return original content if replacement fails


class ChatService:
    """Service for managing chat messages and responses."""

    def __init__(self):
        self.tools_limit = 3  # Default tools limit

    async def _get_next_sequence_order(self, session, conversation_id: str) -> int:
        """Atomically get the next sequence order for a conversation."""
        # Lock the conversation and get max sequence order
        stmt = select(
            func.coalesce(func.max(MessageAttachment.sequence_order), 0)
        ).where(
            MessageAttachment.entity_type == "conversation",
            MessageAttachment.entity_id == conversation_id,
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        return max_order + 1

    @with_db_session
    async def create_user_message(
        self, content: str, session, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a user message and attach it to a conversation."""
        # Get or create conversation
        if conversation_id:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            # Create new conversation
            conversation = Conversation(title="New Chat")
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

        # Apply placeholder replacement to user message content
        processed_content = await replace_message_placeholders(content, conversation.id)

        # Create user message
        user_message = Message(content=processed_content, role="user")
        session.add(user_message)
        await session.commit()
        await session.refresh(user_message)

        # Atomically get next sequence order
        next_sequence_order = await self._get_next_sequence_order(
            session, conversation.id
        )

        # Attach user message to conversation
        user_attachment = MessageAttachment(
            message_id=user_message.id,
            entity_type="conversation",
            entity_id=conversation.id,
            sequence_order=next_sequence_order,
        )
        session.add(user_attachment)
        await session.commit()

        return {
            "message": {
                "id": user_message.id,
                "content": user_message.content,
                "role": user_message.role,
                "created_at": user_message.created_at.isoformat(),
                "conversation_id": conversation.id,
                "sequence_order": next_sequence_order,
            },
            "conversation_id": conversation.id,
        }

    @with_db_session
    async def generate_response(
        self,
        conversation_id: str,
        session,
    ) -> Dict[str, Any]:
        """Generate an assistant response for a conversation."""
        # Get OpenAI settings and sampling parameters
        ai_settings = await ai_service.get_openai_settings()
        sampling_settings = await ai_service.get_sampling_settings()

        if not ai_settings["api_key"]:
            raise ValueError(ERROR_NO_OPENAI_API_KEY)

        # Get conversation history for context
        history_stmt = (
            select(Message)
            .join(MessageAttachment)
            .where(
                MessageAttachment.entity_type == "conversation",
                MessageAttachment.entity_id == conversation_id,
            )
            .order_by(MessageAttachment.sequence_order)
        )

        history_result = await session.execute(history_stmt)
        messages_for_api = []

        # Add system prompt if enabled (include conversation personas)
        system_prompt = await system_prompt_service.build_system_prompt(
            conversation_id=conversation_id
        )
        if system_prompt:
            messages_for_api.append({"role": "system", "content": system_prompt})

        for msg in history_result.scalars():
            messages_for_api.append({"role": msg.role, "content": msg.content})

        # Inject tool prompt and status for unified context
        try:
            enabled_tools = tool_service.get_enabled_tools()
            tool_prompt = tool_service.build_tool_prompt([], enabled_tools)
            status_section = await tool_service.run_auto_tools_and_status(
                enabled_tools, conversation_id=conversation_id
            )
            messages_for_api = [
                m
                for m in messages_for_api
                if not (
                    m.get("role") == "system"
                    and (
                        "tool(s):" in m.get("content", "")
                        or "<STATUS_DASHBOARD>" in m.get("content", "")
                    )
                )
            ]
            messages_for_api.insert(
                0, {"role": "system", "content": tool_prompt + status_section}
            )
        except Exception as _e:
            # Non-fatal; proceed without tool prompt/status if anything fails
            pass

        # Use unified inference loop
        assistant_content = await run_inference_to_completion(
            messages_for_api,
            conversation_id=conversation_id,
            model_name=ai_settings["model_name"],
            api_key=ai_settings["api_key"],
            base_url=ai_settings["base_url"],
            temperature=sampling_settings["temperature"],
            top_p=sampling_settings["top_p"],
            max_tokens=sampling_settings["max_tokens"],
            frequency_penalty=sampling_settings["frequency_penalty"],
            presence_penalty=sampling_settings["presence_penalty"],
            tools_limit=self.tools_limit,
            get_enabled_tools=tool_service.get_enabled_tools,
            build_tool_prompt=tool_service.build_tool_prompt,
            run_auto_tools_and_status=tool_service.run_auto_tools_and_status,
            get_tools_registry=tool_service.get_tools_registry,
        )

        # Create assistant message
        assistant_message = Message(
            content=assistant_content,
            role="assistant",
            extra_data={"model": ai_settings["model_name"]},
        )
        session.add(assistant_message)
        await session.commit()
        await session.refresh(assistant_message)

        # Atomically get next sequence order for assistant message
        assistant_sequence_order = await self._get_next_sequence_order(
            session, conversation_id
        )

        # Attach assistant message to conversation
        assistant_attachment = MessageAttachment(
            message_id=assistant_message.id,
            entity_type="conversation",
            entity_id=conversation_id,
            sequence_order=assistant_sequence_order,
        )
        session.add(assistant_attachment)
        await session.commit()

        return {
            "id": assistant_message.id,
            "content": assistant_message.content,
            "role": assistant_message.role,
            "created_at": assistant_message.created_at.isoformat(),
            "conversation_id": conversation_id,
        }

    @with_db_session
    async def get_streaming_generator(
        self,
        conversation_id: str,
        messages_for_api: List[Dict[str, Any]],
        session,
        is_regeneration: bool = False,
        message_id_to_replace: int = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get async generator for streaming chat responses with unified system message handling."""
        # Get OpenAI settings and sampling parameters
        ai_settings = await ai_service.get_openai_settings()
        sampling_settings = await ai_service.get_sampling_settings()

        if not ai_settings["api_key"]:
            raise ValueError(ERROR_NO_OPENAI_API_KEY)

        # For regeneration, clean up messages after the user message
        if is_regeneration and message_id_to_replace:
            await self._cleanup_messages_for_regeneration(
                conversation_id, message_id_to_replace
            )

        system_message_content = ""
        context_message_content = ""

        # Use unified inference loop
        async for event in inference_loop(
            messages_for_api,
            conversation_id=conversation_id,
            model_name=ai_settings["model_name"],
            api_key=ai_settings["api_key"],
            base_url=ai_settings["base_url"],
            temperature=sampling_settings["temperature"],
            top_p=sampling_settings["top_p"],
            max_tokens=sampling_settings["max_tokens"],
            frequency_penalty=sampling_settings["frequency_penalty"],
            presence_penalty=sampling_settings["presence_penalty"],
            seed=sampling_settings.get("seed"),
            tools_limit=self.tools_limit,
            get_enabled_tools=tool_service.get_enabled_tools,
            build_tool_prompt=tool_service.build_tool_prompt,
            run_auto_tools_and_status=tool_service.run_auto_tools_and_status,
            get_tools_registry=tool_service.get_tools_registry,
        ):
            if event.get("type") == "system_chunk":
                content = event.get("content", "")
                system_message_content += content
                yield event  # Pass through for UI streaming
            elif event.get("type") == "context_chunk":
                content = event.get("content", "")
                context_message_content += content
                yield event  # Pass through for UI streaming
            elif event.get("type") == "system_complete":
                system_content = event.get("content", system_message_content)

                # Apply placeholder replacement to system message content
                processed_system_content = await replace_message_placeholders(
                    system_content, conversation_id
                )

                # Persist system message to database
                system_message = Message(
                    content=processed_system_content,
                    role="system",
                    extra_data={"tool_generated": True},
                )
                session.add(system_message)
                await session.commit()
                await session.refresh(system_message)

                # Get atomic sequence order
                sequence_order = await self._get_next_sequence_order(
                    session, conversation_id
                )
                system_attachment = MessageAttachment(
                    message_id=system_message.id,
                    entity_type="conversation",
                    entity_id=conversation_id,
                    sequence_order=sequence_order,
                )
                session.add(system_attachment)
                await session.commit()

                # Emit system_complete with persisted message info
                yield {
                    "type": "system_complete",
                    "content": processed_system_content,
                    "message": {
                        "id": system_message.id,
                        "content": processed_system_content,
                        "role": "system",
                        "created_at": system_message.created_at.isoformat(),
                        "conversation_id": conversation_id,
                        "sequence_order": sequence_order,
                    },
                }
                system_message_content = ""  # Reset for next system message
            elif event.get("type") == "context_complete":
                context_content = event.get("content", context_message_content)

                # Apply placeholder replacement to context message content
                processed_context_content = await replace_message_placeholders(
                    context_content, conversation_id
                )

                # Persist context message to database with role "tool"
                context_message = Message(
                    content=processed_context_content,
                    role="tool",
                    extra_data={"tool_generated": True},
                )
                session.add(context_message)
                await session.commit()
                await session.refresh(context_message)

                # Get atomic sequence order
                sequence_order = await self._get_next_sequence_order(
                    session, conversation_id
                )
                context_attachment = MessageAttachment(
                    message_id=context_message.id,
                    entity_type="conversation",
                    entity_id=conversation_id,
                    sequence_order=sequence_order,
                )
                session.add(context_attachment)
                await session.commit()

                # Emit context_complete with persisted message info
                yield {
                    "type": "context_complete",
                    "content": processed_context_content,
                    "message": {
                        "id": context_message.id,
                        "content": processed_context_content,
                        "role": "tool",
                        "created_at": context_message.created_at.isoformat(),
                        "conversation_id": conversation_id,
                        "sequence_order": sequence_order,
                    },
                }
                context_message_content = ""  # Reset for next context message
            elif event.get("type") == "complete":
                # Handle final assistant message persistence
                final_content = event.get("content", "")

                if is_regeneration and message_id_to_replace:
                    # Update existing message for regeneration
                    stmt = select(Message).where(Message.id == message_id_to_replace)
                    result = await session.execute(stmt)
                    message = result.scalar_one_or_none()
                    if message:
                        message.content = final_content

                        # Update sequence_order to ensure it comes after any new system messages
                        attachment_stmt = select(MessageAttachment).where(
                            MessageAttachment.message_id == message_id_to_replace
                        )
                        attachment_result = await session.execute(attachment_stmt)
                        attachment = attachment_result.scalar_one_or_none()
                        if attachment:
                            new_sequence_order = await self._get_next_sequence_order(
                                session, conversation_id
                            )
                            attachment.sequence_order = new_sequence_order

                        await session.commit()
                        await session.refresh(message)

                        yield {
                            "type": "message_complete",
                            "content": final_content,
                            "message": {
                                "id": message.id,
                                "content": final_content,
                                "role": "assistant",
                                "created_at": message.created_at.isoformat(),
                                "conversation_id": conversation_id,
                                "sequence_order": (
                                    attachment.sequence_order if attachment else None
                                ),
                            },
                        }
                    else:
                        yield {
                            "type": "error",
                            "message": ERROR_MESSAGE_NOT_FOUND_REGEN,
                        }
                else:
                    # Create new assistant message for regular chat
                    assistant_message = Message(
                        content=final_content,
                        role="assistant",
                        extra_data={"model": ai_settings["model_name"]},
                    )
                    session.add(assistant_message)
                    await session.commit()
                    await session.refresh(assistant_message)

                    # Get atomic sequence order
                    sequence_order = await self._get_next_sequence_order(
                        session, conversation_id
                    )
                    assistant_attachment = MessageAttachment(
                        message_id=assistant_message.id,
                        entity_type="conversation",
                        entity_id=conversation_id,
                        sequence_order=sequence_order,
                    )
                    session.add(assistant_attachment)
                    await session.commit()

                    yield {
                        "type": "message_complete",
                        "content": final_content,
                        "message": {
                            "id": assistant_message.id,
                            "content": final_content,
                            "role": "assistant",
                            "created_at": assistant_message.created_at.isoformat(),
                            "conversation_id": conversation_id,
                            "sequence_order": sequence_order,
                        },
                    }
            else:
                # Pass through all other events unchanged
                yield event

    @with_db_session
    async def _cleanup_messages_for_regeneration(
        self, conversation_id: str, message_id_to_replace: int, session
    ):
        """Delete all messages (including system messages) after the user message that prompted the assistant response being regenerated."""
        # Find the assistant message being replaced
        stmt = (
            select(MessageAttachment)
            .where(
                MessageAttachment.entity_type == "conversation",
                MessageAttachment.entity_id == conversation_id,
            )
            .join(Message)
            .where(Message.id == message_id_to_replace)
        )
        result = await session.execute(stmt)
        assistant_attachment = result.scalar_one_or_none()

        if not assistant_attachment:
            return  # Message not found, nothing to clean up

        # Find the most recent user message before the assistant message
        user_message_order = None
        all_attachments_stmt = (
            select(MessageAttachment)
            .where(
                MessageAttachment.entity_type == "conversation",
                MessageAttachment.entity_id == conversation_id,
                MessageAttachment.sequence_order < assistant_attachment.sequence_order,
            )
            .join(Message)
            .order_by(MessageAttachment.sequence_order.desc())
        )

        all_result = await session.execute(all_attachments_stmt)
        for attachment in all_result.scalars():
            message_stmt = select(Message).where(Message.id == attachment.message_id)
            message_result = await session.execute(message_stmt)
            message = message_result.scalar_one_or_none()
            if message and message.role == "user":
                user_message_order = attachment.sequence_order
                break

        if user_message_order is None:
            return  # No user message found, nothing to clean up

        # Delete all messages after the user message EXCEPT the message being regenerated
        messages_to_delete_stmt = select(MessageAttachment).where(
            MessageAttachment.entity_type == "conversation",
            MessageAttachment.entity_id == conversation_id,
            MessageAttachment.sequence_order > user_message_order,
        )
        messages_to_delete_result = await session.execute(messages_to_delete_stmt)

        for attachment in messages_to_delete_result.scalars():
            # Skip the message we're regenerating - don't delete it
            if attachment.message_id == message_id_to_replace:
                continue

            # Delete other messages (cascade will handle the attachment)
            message_stmt = select(Message).where(Message.id == attachment.message_id)
            message_result = await session.execute(message_stmt)
            message = message_result.scalar_one_or_none()
            if message:
                await session.delete(message)

        await session.commit()

    @with_db_session
    async def update_message(
        self, message_id: int, content: str, session
    ) -> Dict[str, Any]:
        """Update a message's content."""
        # Find the message to update
        stmt = select(Message).where(Message.id == message_id)
        result = await session.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError(ERROR_MESSAGE_NOT_FOUND)

        # Update the content
        message.content = content
        await session.commit()
        await session.refresh(message)

        return {
            "id": message.id,
            "content": message.content,
            "updated_at": message.updated_at.isoformat(),
        }

    @with_db_session
    async def delete_message(self, message_id: int, session) -> Dict[str, Any]:
        """Delete a message and its attachments."""
        # Find the message to delete
        stmt = select(Message).where(Message.id == message_id)
        result = await session.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError(ERROR_MESSAGE_NOT_FOUND)

        # Delete the message (cascade will handle message attachments automatically!)
        await session.delete(message)
        await session.commit()

        return {"message": "Message deleted successfully", "deleted_id": message_id}

    @with_db_session
    async def regenerate_message(
        self, conversation_id: str, message_id_to_replace: int, session
    ) -> Dict[str, Any]:
        """Regenerate an assistant's response."""
        # Find the message to replace
        stmt = select(Message).where(Message.id == message_id_to_replace)
        result = await session.execute(stmt)
        message_to_replace = result.scalar_one_or_none()

        if not message_to_replace:
            raise ValueError(ERROR_MESSAGE_NOT_FOUND)

        if message_to_replace.role != "assistant":
            raise ValueError("Can only regenerate assistant messages")

        # Get conversation history for context (up to but not including the message being replaced)
        history_stmt = (
            select(Message)
            .join(MessageAttachment)
            .where(
                MessageAttachment.entity_type == "conversation",
                MessageAttachment.entity_id == conversation_id,
            )
            .order_by(MessageAttachment.sequence_order)
        )

        history_result = await session.execute(history_stmt)
        messages_for_api = []

        # Add system prompt if enabled (include conversation personas)
        system_prompt = await system_prompt_service.build_system_prompt(
            conversation_id=conversation_id
        )
        if system_prompt:
            messages_for_api.append({"role": "system", "content": system_prompt})

        # Add conversation history up to (but not including) the message being replaced
        # Only include messages up to the last user message before the regenerated message
        messages_to_include = []
        last_user_message = None

        for msg in history_result.scalars():
            if msg.id == message_id_to_replace:
                break  # Stop before the message we're replacing!

            messages_to_include.append(msg)
            if msg.role == "user":
                last_user_message = msg

        # Only include messages up to and including the last user message
        # This excludes any system messages that came after the user's prompt
        if last_user_message:
            for msg in messages_to_include:
                messages_for_api.append({"role": msg.role, "content": msg.content})
                if msg.id == last_user_message.id:
                    break  # Stop after the last user message

        # The user prompt is already included in the conversation history,
        # so no need to duplicate it here

        # Get AI settings
        ai_settings = await ai_service.get_openai_settings()
        sampling_settings = await ai_service.get_sampling_settings()

        if not ai_settings["api_key"]:
            raise ValueError(ERROR_NO_OPENAI_API_KEY)

        # Rebuild base messages with latest system prompt
        try:
            system_prompt = await system_prompt_service.build_system_prompt(
                conversation_id=conversation_id
            )
            base_messages = list(messages_for_api)
            if system_prompt:
                if base_messages and base_messages[0].get("role") == "system":
                    base_messages[0]["content"] = system_prompt
                else:
                    base_messages.insert(
                        0, {"role": "system", "content": system_prompt}
                    )
        except Exception:
            base_messages = list(messages_for_api)

        new_content = await run_inference_to_completion(
            base_messages,
            conversation_id=conversation_id,
            model_name=ai_settings["model_name"],
            api_key=ai_settings["api_key"],
            base_url=ai_settings["base_url"],
            temperature=sampling_settings["temperature"],
            top_p=sampling_settings["top_p"],
            max_tokens=sampling_settings["max_tokens"],
            frequency_penalty=sampling_settings["frequency_penalty"],
            presence_penalty=sampling_settings["presence_penalty"],
            seed=sampling_settings.get("seed"),
            tools_limit=self.tools_limit,
            get_enabled_tools=tool_service.get_enabled_tools,
            build_tool_prompt=tool_service.build_tool_prompt,
            run_auto_tools_and_status=tool_service.run_auto_tools_and_status,
            get_tools_registry=tool_service.get_tools_registry,
        )

        # Update the existing message instead of creating a new one!
        message_to_replace.content = new_content
        await session.commit()
        await session.refresh(message_to_replace)

        return {
            "message": {
                "id": message_to_replace.id,
                "content": message_to_replace.content,
                "role": message_to_replace.role,
                "created_at": message_to_replace.created_at.isoformat(),
                "conversation_id": conversation_id,
            }
        }

    async def prepare_conversation_messages(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Prepare conversation messages for API consumption.

        Moved from chat router to centralize message preparation logic.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of messages formatted for API calls
        """
        from services.conversation_service import conversation_service

        # Get conversation messages
        conv_data = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id
        )
        messages = conv_data["messages"]

        # Build messages for API
        base_messages = []

        # Add system prompt if enabled
        system_prompt = await system_prompt_service.build_system_prompt(
            conversation_id=conversation_id
        )
        if system_prompt:
            base_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            base_messages.append({"role": msg["role"], "content": msg["content"]})

        return base_messages

    async def prepare_regeneration_messages(
        self, conversation_id: str, message_id_to_replace: int
    ) -> List[Dict[str, Any]]:
        """Prepare messages for regeneration, excluding the message being replaced.

        Moved from chat router to centralize regeneration message logic.

        Args:
            conversation_id: ID of the conversation
            message_id_to_replace: ID of the message being regenerated

        Returns:
            List of messages formatted for API calls, up to last user message
        """
        from services.conversation_service import conversation_service

        # Get conversation messages for context
        conv_data = await conversation_service.get_conversation_messages(
            conversation_id
        )
        messages = conv_data["messages"]

        # Build messages for API (up to but not including the message being replaced)
        messages_for_api = []

        # Add system prompt if enabled (include conversation personas)
        system_prompt = await system_prompt_service.build_system_prompt(
            conversation_id=conversation_id
        )
        if system_prompt:
            messages_for_api.append({"role": "system", "content": system_prompt})

        # Add conversation history up to and including the last user message before the message being replaced
        # Find the last user message before the message being replaced
        messages_to_include = []
        last_user_message_index = -1

        for i, msg in enumerate(messages):
            if msg["id"] == message_id_to_replace:
                break  # Stop before the message we're replacing!
            messages_to_include.append(msg)
            if msg["role"] == "user":
                last_user_message_index = i

        # Only include messages up to and including the last user message
        # This excludes any system messages that came after the user's prompt
        if last_user_message_index >= 0:
            for i in range(last_user_message_index + 1):
                msg = messages_to_include[i]
                messages_for_api.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        return messages_for_api


async def _prepare_loop_iteration(
    base_messages: List[Dict[str, Any]],
    tools_used: List[str],
    conversation_id: str,
    tools_limit: int,
    get_enabled_tools,
    build_tool_prompt,
    run_auto_tools_and_status,
) -> Dict[str, Any]:
    """Prepare messages and tools for a single loop iteration.

    Returns:
        Dict containing 'messages_for_api' and 'available_tools'
    """
    print("Going to get enabled tools")
    enabled_tools = get_enabled_tools()
    num_tools_used = len([name for name in tools_used if name])
    print("Going to get status section")
    status_section = await run_auto_tools_and_status(
        enabled_tools, conversation_id=conversation_id
    )
    print("Going to get other hsit")

    # Remove existing tool prompt/status in base messages
    messages_for_api = [
        m
        for m in base_messages
        if not (
            m.get("role") == "system"
            and (
                "tool(s):" in m.get("content", "")
                or "<STATUS_DASHBOARD>" in m.get("content", "")
            )
        )
    ]
    status_message = {"role": "system", "content": status_section}
    messages_for_api.insert(0, status_message)

    # Initialize available_tools list
    available_tools = []

    # Only populate tools if limit hasn't been reached
    if num_tools_used < tools_limit:
        tool_prompt = build_tool_prompt(tools_used, enabled_tools)
        messages_for_api.insert(0, {"role": "system", "content": tool_prompt})
        print(str(tools_limit - num_tools_used) + " left")
        # Filter available tools
        available_tools = await _filter_available_tools(enabled_tools, tools_used)

    return {
        "messages_for_api": messages_for_api,
        "available_tools": available_tools,
        "enabled_tools": enabled_tools,
        "num_tools_used": num_tools_used,
    }


async def _prepare_api_request(
    messages_for_api: List[Dict[str, Any]],
    available_tools: List[Dict[str, Any]],
    conversation_id: str,
    model_name: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    frequency_penalty: float,
    presence_penalty: float,
    seed: int = None,
) -> Dict[str, Any]:
    """Build the OpenAI API request parameters."""

    # Log all parameters being sent to OpenAI API
    api_params = {
        "model": model_name,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "tools_count": len(available_tools),
        "stream": True,
    }
    if seed != -1:
        api_params["seed"] = seed
    print(f"[OpenAI API Call] Parameters: {api_params}")

    # Replace placeholders in messages before sending to API
    processed_messages = []
    for message in messages_for_api:
        if "content" in message and message["content"]:
            processed_content = await replace_message_placeholders(
                message["content"], conversation_id
            )
            processed_message = message.copy()
            processed_message["content"] = processed_content
            processed_messages.append(processed_message)
        else:
            processed_messages.append(message)

    print("Preparing response", processed_messages)

    # Prepare API call parameters
    api_call_params = {
        "model": model_name,
        "messages": processed_messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "tools": available_tools,
        "stream": True,
    }

    # Add optional parameters if they exist
    if seed is not None:
        api_call_params["seed"] = seed

    return api_call_params


def _should_continue_loop(
    tool_call_detected: bool,
    streaming_interrupted: bool,
    tool_call_name: str,
    collected_args: str,
    base_messages: List[Dict[str, Any]],
) -> bool:
    """Determine if the inference loop should continue.

    Returns:
        True if loop should continue, False if it should break
    """
    # Check for incomplete tool calls
    if tool_call_detected and not streaming_interrupted:
        print(
            "[TOOL_CALL_DEBUG] *** WARNING: Tool call was detected but never completed with finish_reason='tool_calls' ***"
        )
        print(
            f"[TOOL_CALL_DEBUG] Incomplete tool call state: name={tool_call_name}, args='{collected_args}'"
        )

    # If no tool call was detected, we are done
    if not tool_call_detected:
        final_message_tool_calls = len(
            [
                m
                for m in base_messages
                if m.get("role") == "assistant" and m.get("tool_calls")
            ]
        )
        print(
            f"[TOOL_CALL_DEBUG] No tool call detected - exiting loop. Final message history has {final_message_tool_calls} assistant messages with tool_calls"
        )
        return False  # Break the loop

    # If tool call was detected, continue the loop
    return True


async def _filter_available_tools(
    enabled_tools: List[Dict[str, Any]], tools_used: List[str]
) -> List[Dict[str, Any]]:
    """Filter tools based on conditions, one-time usage, etc."""
    available_tools = []

    for t in enabled_tools:
        if t.get("auto_tool"):
            continue
        if not callable(t.get("function")):
            continue
        name = t.get("schema", {}).get("name")
        if t.get("one_time") and name in tools_used:
            continue

        # Check condition if present
        condition_fn = t.get("condition")
        if condition_fn and callable(condition_fn):
            try:
                if asyncio.iscoroutinefunction(condition_fn):
                    condition_result = await condition_fn()
                else:
                    condition_result = condition_fn()
                    if asyncio.iscoroutine(condition_result):
                        condition_result = await condition_result

                if not condition_result:
                    continue  # Skip this tool if condition is False
            except Exception as e:
                print(f"[Ghostpad] Condition check failed for {name}: {e}")
                continue  # Skip on error

        available_tools.append({"type": "function", "function": t.get("schema")})

    return available_tools


def _find_tool_by_name(
    tool_name: str, registry: Dict[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Find a tool in the registry by schema name."""
    for t in registry.values():
        if t.get("enabled") and t.get("schema", {}).get("name") == tool_name:
            return t
    return None


async def _process_streaming_response(
    response,
    available_tools: List[Dict[str, Any]],
    final_content: str,
    conversation_id: str,
    model_name: str,
    tools_used: List[str],
    get_tools_registry,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Process the streaming response and detect tool calls."""
    tool_call_detected = False
    collected_args = ""
    tool_call_name = None
    streaming_interrupted = False
    updated_final_content = final_content

    print(
        f"[TOOL_CALL_DEBUG] Starting streaming response - available_tools count: {len(available_tools)}"
    )

    try:
        async for chunk in response:
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                # Stream content only if not in a tool call sequence
                if not tool_call_detected:
                    updated_final_content += delta.content
                    yield {"type": "chunk", "content": delta.content}
                continue

            # Handle tool call streaming
            tool_call_detected, tool_call_name, collected_args = (
                _handle_tool_call_streaming(
                    delta, tool_call_detected, tool_call_name, collected_args
                )
            )

            finish_reason = chunk.choices[0].finish_reason
            print(
                f"[TOOL_CALL_DEBUG] Chunk finish_reason: {finish_reason}, tool_call_detected: {tool_call_detected}"
            )

            # Check if streaming ended unexpectedly
            if finish_reason and tool_call_detected and finish_reason != "tool_calls":
                print(
                    f"[TOOL_CALL_DEBUG] *** WARNING: Tool call streaming ended with unexpected finish_reason: {finish_reason} ***"
                )
                streaming_interrupted = True

            if tool_call_detected and finish_reason == "tool_calls":
                # Parse tool arguments
                args = _parse_tool_arguments(collected_args)
                print(f"[DEBUG] Tool call: {tool_call_name} with args: {args}")

                # Find tool by schema name
                registry = get_tools_registry()
                selected = _find_tool_by_name(tool_call_name, registry)

                # Initialize variables for tool execution results
                tool_result = None
                streamed_accumulator = []
                context_messages_accumulator = []
                system_messages_accumulator = []
                response_context = None

                if selected is None:
                    tool_result = f"Unknown function: {tool_call_name}"
                else:
                    # Execute tool function using extracted method
                    async for event in _execute_tool_function(
                        selected,
                        args,
                        conversation_id,
                        model_name,
                        tools_used,
                        updated_final_content,
                    ):
                        if event["type"] == "tool_execution_complete":
                            # Extract results from tool execution
                            tool_result = event["tool_result"]
                            streamed_accumulator = event["streamed_accumulator"]
                            context_messages_accumulator = event[
                                "context_messages_accumulator"
                            ]
                            system_messages_accumulator = event[
                                "system_messages_accumulator"
                            ]
                            updated_final_content = event["updated_final_content"]
                            response_context = event["response_context"]
                        else:
                            # Forward streaming events
                            yield event

                # Return tool execution results
                yield {
                    "type": "tool_call_complete",
                    "tool_call_name": tool_call_name,
                    "tool_result": tool_result,
                    "streamed_accumulator": streamed_accumulator,
                    "context_messages_accumulator": context_messages_accumulator,
                    "system_messages_accumulator": system_messages_accumulator,
                    "updated_final_content": updated_final_content,
                    "response_context": response_context,
                    "args": args,
                }
                return

    except Exception as streaming_error:
        print(f"[TOOL_CALL_DEBUG] *** STREAMING EXCEPTION: {streaming_error} ***")
        print("[TOOL_CALL_DEBUG] State when exception occurred:")
        print(f"[TOOL_CALL_DEBUG]   - tool_call_detected: {tool_call_detected}")
        print(f"[TOOL_CALL_DEBUG]   - tool_call_name: {tool_call_name}")
        print(f"[TOOL_CALL_DEBUG]   - collected_args: '{collected_args}'")
        print(f"[TOOL_CALL_DEBUG]   - collected_args_length: {len(collected_args)}")

        # If we were in the middle of a tool call, this is likely the diff error
        if tool_call_detected:
            print(
                "[TOOL_CALL_DEBUG] *** LIKELY CAUSE: llama.cpp diff error during tool call streaming ***"
            )
            print("[TOOL_CALL_DEBUG] Tool call was incomplete when streaming crashed")

        # Re-raise to maintain error behavior but with better context
        raise streaming_error

    # Return final results if no tool call was detected
    yield {
        "type": "streaming_complete",
        "tool_call_detected": tool_call_detected,
        "streaming_interrupted": streaming_interrupted,
        "tool_call_name": tool_call_name,
        "collected_args": collected_args,
        "updated_final_content": updated_final_content,
    }


def _handle_tool_call_streaming(
    delta, tool_call_detected: bool, tool_call_name: Optional[str], collected_args: str
) -> tuple[bool, Optional[str], str]:
    """Handle tool call argument collection from streaming chunks."""
    if getattr(delta, "tool_calls", None):
        tool_call_detected = True
        print(
            f"[TOOL_CALL_DEBUG] Tool call detected in streaming chunk - delta.tool_calls count: {len(delta.tool_calls)}"
        )
        for tc in delta.tool_calls:
            if tc.function:
                if tool_call_name is None:
                    tool_call_name = tc.function.name
                    print(
                        f"[TOOL_CALL_DEBUG] First tool call detected: {tc.function.name}"
                    )
                if tc.function.arguments:
                    collected_args += tc.function.arguments
                    print(
                        f"[TOOL_CALL_DEBUG] Collecting args chunk: '{tc.function.arguments}', total length now: {len(collected_args)}"
                    )

    return tool_call_detected, tool_call_name, collected_args


async def _process_tool_call_completion(
    event: Dict[str, Any],
    base_messages: List[Dict[str, Any]],
    tools_used: List[str],
    tool_call_results: List[str],
    conversation_id: str,
    collected_args: str,
) -> tuple[bool, bool, str]:
    """Process tool call completion event and update conversation history.

    Returns:
        tuple of (tool_call_detected, streaming_interrupted, final_content)
    """
    # Extract tool execution results
    tool_call_name = event["tool_call_name"]
    streamed_accumulator = event["streamed_accumulator"]
    system_messages_accumulator = event["system_messages_accumulator"]
    context_messages_accumulator = event["context_messages_accumulator"]
    final_content = event["updated_final_content"]
    response_context = event["response_context"]
    args = event["args"]

    tool_call_detected = True
    streaming_interrupted = False

    # Track usage
    tools_used.append(tool_call_name or "")

    # Build parameter string for logging
    param_str = (
        ", ".join(f"{k}={json.dumps(v)}" for k, v in (args or {}).items())
        if args
        else "(no parameters)"
    )
    tool_call_results.append(
        f"[{datetime.now().isoformat()}] You called `{tool_call_name}` with parameters: {param_str}."
    )

    # Clean up old tool call history messages
    base_messages[:] = [
        m
        for m in base_messages
        if not (
            m.get("role") == "system"
            and m.get("content", "").startswith("Tool Call(s) Made:")
        )
    ]

    # Add the assistant's tool call message to the conversation
    tool_call_id = f"call_{len(tools_used)}"
    base_messages.append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_call_name,
                        "arguments": collected_args,
                    },
                }
            ],
        }
    )

    # Add any accumulated system messages to conversation history
    if system_messages_accumulator:
        # Combine all system messages from streaming
        combined_system_content = "".join(system_messages_accumulator)
        # Apply placeholder replacement before adding to conversation history
        processed_combined_content = await replace_message_placeholders(
            combined_system_content, conversation_id
        )
        base_messages.append(
            {
                "role": "system",
                "content": processed_combined_content,
            }
        )

    # Check if tool generated system content via response_context (non-streaming)
    system_content = response_context.get_system_content() if response_context else ""
    if system_content:
        # Apply placeholder replacement before adding to conversation history
        processed_system_content = await replace_message_placeholders(
            system_content, conversation_id
        )
        # Add system message to conversation history so AI can see it in subsequent iterations
        base_messages.append({"role": "system", "content": processed_system_content})

    # Add any accumulated context messages to conversation history
    if context_messages_accumulator:
        # Combine all context messages from streaming
        combined_context_content = "".join(context_messages_accumulator)
        # Apply placeholder replacement before adding to conversation history
        processed_combined_context_content = await replace_message_placeholders(
            combined_context_content, conversation_id
        )
        base_messages.append(
            {
                "role": "tool",
                "content": processed_combined_context_content,
            }
        )

    # Add tool result and any streamed content to conversation so model can see it
    # Prefer the streamed content if present, otherwise fall back to the tool_result string.
    combined_streamed = "".join(streamed_accumulator) if streamed_accumulator else ""
    # Also include any lingering content from the response_context if not already captured
    try:
        fc = response_context.get_all_content() if response_context else ""
    except Exception:
        fc = ""
    if fc and fc not in combined_streamed:
        combined_streamed = combined_streamed + fc

    return tool_call_detected, streaming_interrupted, final_content


def _parse_tool_arguments(collected_args: str) -> Dict[str, Any]:
    """Parse and validate tool call arguments from JSON."""
    try:
        # Handle potential duplicate JSON by taking only the first valid JSON object
        if collected_args:
            # Find the first complete JSON object
            brace_count = 0
            first_json_end = -1
            for i, char in enumerate(collected_args):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        first_json_end = i + 1
                        break

            if first_json_end > 0:
                first_json = collected_args[:first_json_end]
                args = json.loads(first_json)
                print(
                    f"[DEBUG] Extracted first JSON: '{first_json}', parsed args: {args}"
                )
            else:
                args = json.loads(collected_args)
        else:
            args = {}
    except Exception as e:
        print(
            f"[TOOL_CALL_DEBUG] JSON parse error: {e}, collected_args was: '{collected_args}', length: {len(collected_args)}"
        )
        args = {}

    return args


async def _execute_tool_function(
    tool: Dict[str, Any],
    args: Dict[str, Any],
    conversation_id: str,
    model_name: str,
    tools_used: List[str],
    final_content: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute a tool function and handle streaming/system content."""
    tool_fn = tool.get("function")

    # Create response context for tool streaming
    inference_context = {
        "tool_streamed_content": [],
        "system_streamed_content": [],
        "final_content": final_content,
    }

    response_context = ResponseContext(inference_context)

    # Create metadata object for tools that support it
    metadata = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "model_name": model_name,
        "tool_call_count": len(tools_used) + 1,
    }

    # Check which parameters the tool function accepts
    sig = inspect.signature(tool_fn)
    supports_metadata = "metadata" in sig.parameters

    # Prepare tool call kwargs based on what the tool supports
    tool_kwargs = dict(args)
    if supports_metadata:
        tool_kwargs["metadata"] = metadata

    print(f"[DEBUG] Final tool_kwargs: {tool_kwargs}")

    # Call the tool function
    if inspect.iscoroutinefunction(tool_fn):
        tool_result = await tool_fn(**tool_kwargs)
    else:
        res = tool_fn(**tool_kwargs)
        tool_result = await res if inspect.iscoroutine(res) else res

    # Prepare accumulator for any streamed chunks so we can persist them
    streamed_accumulator = []
    system_messages_accumulator = []
    context_messages_accumulator = []
    system_chunks_from_generator = []
    context_chunks_from_generator = []
    updated_final_content = final_content

    # Check if the tool result is a generator (for real-time streaming)
    if hasattr(tool_result, "__aiter__") or hasattr(tool_result, "__iter__"):
        # Check if tool uses system message streaming
        system_content = response_context.get_system_content()
        if system_content:
            # Tool used system streaming - flush assistant message first, then stream system
            if updated_final_content.strip():
                yield {"type": "assistant_complete", "content": updated_final_content}
                updated_final_content = ""  # Reset for potential continuation

            yield {"type": "system_message_start"}
            yield {"type": "system_chunk", "content": system_content}
            yield {"type": "system_complete", "content": system_content}
            tool_result = "Tool output sent as system message"
        else:
            # Tool yields ResponseChunk objects
            if hasattr(tool_result, "__aiter__"):
                # Async generator
                async for chunk in tool_result:
                    if chunk:
                        if chunk.type == "system":
                            yield {"type": "system_chunk", "content": chunk.content}
                            # Accumulate system chunks for system_complete event
                            system_chunks_from_generator.append(chunk.content)
                        elif chunk.type == "context":
                            yield {"type": "context_chunk", "content": chunk.content}
                            # Accumulate context chunks for context_complete event
                            context_chunks_from_generator.append(chunk.content)
                        else:  # assistant chunk
                            processed_chunk_content = await replace_message_placeholders(chunk.content, conversation_id)
                            updated_final_content += processed_chunk_content
                            streamed_accumulator.append(processed_chunk_content)
                            yield {"type": "chunk", "content": processed_chunk_content}
            else:
                # Regular generator
                for chunk in tool_result:
                    if chunk:
                        if chunk.type == "system":
                            yield {"type": "system_chunk", "content": chunk.content}
                            # Accumulate system chunks for system_complete event
                            system_chunks_from_generator.append(chunk.content)
                        elif chunk.type == "context":
                            yield {"type": "context_chunk", "content": chunk.content}
                            # Accumulate context chunks for context_complete event
                            context_chunks_from_generator.append(chunk.content)
                        else:  # assistant chunk
                            processed_chunk_content = await replace_message_placeholders(chunk.content, conversation_id)
                            updated_final_content += processed_chunk_content
                            streamed_accumulator.append(processed_chunk_content)
                            yield {"type": "chunk", "content": processed_chunk_content}

            # After generator completes, emit system_complete if we had system chunks
            if system_chunks_from_generator:
                combined_system_content = await replace_message_placeholders(
                    "".join(system_chunks_from_generator), conversation_id
                )
                yield {"type": "system_complete", "content": combined_system_content}
                system_messages_accumulator.append(combined_system_content)

            # After generator completes, emit context_complete if we had context chunks
            if context_chunks_from_generator:
                combined_context_content = await replace_message_placeholders(
                    "".join(context_chunks_from_generator), conversation_id
                )
                context_messages_accumulator.append(combined_context_content)
                yield {"type": "context_complete", "content": combined_context_content}

            tool_result = "Generator tool completed"
    else:
        # Check if tool used system message streaming - if so, flush assistant message first
        system_content = response_context.get_system_content()
        if system_content:
            # Flush current assistant message before system message
            if updated_final_content.strip():
                yield {"type": "assistant_complete", "content": updated_final_content}
                updated_final_content = ""  # Reset for potential continuation

            yield {"type": "system_message_start"}
            yield {"type": "system_chunk", "content": system_content}
            yield {"type": "system_complete", "content": system_content}

        # Process any streamed content from the tool (via ResponseContext) - still goes to assistant
        if inference_context.get("tool_streamed_content"):
            for streamed_chunk in inference_context["tool_streamed_content"]:
                updated_final_content += streamed_chunk
                streamed_accumulator.append(streamed_chunk)
                yield {"type": "chunk", "content": streamed_chunk}

        # Process any final content appended to the response
        final_content_from_tool = response_context.get_final_content()
        if final_content_from_tool:
            updated_final_content += final_content_from_tool
            streamed_accumulator.append(final_content_from_tool)
            yield {"type": "chunk", "content": final_content_from_tool}

    # Return execution results
    yield {
        "type": "tool_execution_complete",
        "tool_result": tool_result,
        "streamed_accumulator": streamed_accumulator,
        "system_messages_accumulator": system_messages_accumulator,
        "context_messages_accumulator": context_messages_accumulator,
        "updated_final_content": updated_final_content,
        "response_context": response_context,
    }


async def inference_loop(
    base_messages: List[Dict[str, Any]],
    *,
    conversation_id: str | None,
    model_name: str,
    api_key: str,
    base_url: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    frequency_penalty: float,
    presence_penalty: float,
    seed: int = None,
    tools_limit: int,
    get_enabled_tools,
    build_tool_prompt,
    run_auto_tools_and_status,
    get_tools_registry,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Async generator that yields events for a single assistant response using unified tool pipeline.

    Yields dict events: { 'type': 'start' | 'chunk' | 'complete', ... }
    - 'start': indicates beginning of streaming
    - 'chunk': has 'content'
    - 'complete': has 'content' (full final content)
    """
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        yield {"type": "start"}

        tools_used: List[str] = []
        tool_call_results: List[str] = []
        final_content: str = ""

        # Track tool call state for validation
        previous_tool_call_count = 0
        loop_iteration = 0

        while True:
            loop_iteration += 1
            print(f"[TOOL_CALL_DEBUG] === LOOP ITERATION {loop_iteration} START ===")
            # Prepare loop iteration
            iteration_data = await _prepare_loop_iteration(
                base_messages,
                tools_used,
                conversation_id,
                tools_limit,
                get_enabled_tools,
                build_tool_prompt,
                run_auto_tools_and_status,
            )

            messages_for_api = iteration_data["messages_for_api"]
            available_tools = iteration_data["available_tools"]
            enabled_tools = iteration_data["enabled_tools"]

            # LOG: Track message state at start of loop
            current_msg_tool_calls = sum(
                1
                for msg in messages_for_api
                if msg.get("role") == "assistant" and msg.get("tool_calls")
            )

            # VALIDATION: Check if tool calls decreased from previous iteration
            if current_msg_tool_calls < previous_tool_call_count:
                print(
                    f"[TOOL_CALL_DEBUG] *** WARNING: TOOL CALL COUNT DECREASED! Previous: {previous_tool_call_count}, Current: {current_msg_tool_calls} ***"
                )

            previous_tool_call_count = current_msg_tool_calls

            # Prepare API request
            api_call_params = await _prepare_api_request(
                messages_for_api,
                available_tools,
                conversation_id,
                model_name,
                temperature,
                top_p,
                max_tokens,
                frequency_penalty,
                presence_penalty,
                seed,
            )

            response = await client.chat.completions.create(**api_call_params)

            tool_call_detected = False
            collected_args = ""
            tool_call_name = None
            streaming_interrupted = False

            # Process streaming response using extracted method
            async for event in _process_streaming_response(
                response,
                available_tools,
                final_content,
                conversation_id,
                model_name,
                tools_used,
                get_tools_registry,
            ):
                if event["type"] == "tool_call_complete":
                    # Process tool call completion using extracted method
                    tool_call_detected, streaming_interrupted, final_content = (
                        await _process_tool_call_completion(
                            event,
                            base_messages,
                            tools_used,
                            tool_call_results,
                            conversation_id,
                            collected_args,
                        )
                    )
                    continue
                elif event["type"] == "streaming_complete":
                    # Handle case where no tool call was detected
                    tool_call_detected = event["tool_call_detected"]
                    streaming_interrupted = event["streaming_interrupted"]
                    tool_call_name = event["tool_call_name"]
                    collected_args = event["collected_args"]
                    final_content = event["updated_final_content"]
                else:
                    # Forward other events (like chunks)
                    yield event

            # Check if loop should continue
            if not _should_continue_loop(
                tool_call_detected,
                streaming_interrupted,
                tool_call_name,
                collected_args,
                base_messages,
            ):
                break

        completion_message_tool_calls = len(
            [
                m
                for m in base_messages
                if m.get("role") == "assistant" and m.get("tool_calls")
            ]
        )
        print(
            f"[TOOL_CALL_DEBUG] Inference complete - final message history has {completion_message_tool_calls} assistant messages with tool_calls"
        )
        yield {"type": "complete", "content": final_content}
    except Exception as e:
        yield {"type": "error", "message": str(e)}
    finally:
        # Run any registered cleanup functions from enabled tools. These are
        # intended to perform end-of-response cleanup (e.g., consume guidance
        # that should only be cleared once the full response is complete).
        try:
            enabled_tools = get_enabled_tools()
            for t in enabled_tools:
                cleanup_fn = t.get("cleanup_function")
                if callable(cleanup_fn):
                    try:
                        if asyncio.iscoroutinefunction(cleanup_fn):
                            await cleanup_fn()
                        else:
                            res = cleanup_fn()
                            if asyncio.iscoroutine(res):
                                await res
                    except Exception as ce:
                        print(
                            f"[Ghostpad] Cleanup function error for tool {t.get('schema', {}).get('name')}: {ce}"
                        )
        except Exception as e:
            print(f"[Ghostpad] Error running cleanup functions: {e}")


async def run_inference_to_completion(
    base_messages: List[Dict[str, Any]],
    conversation_id: str,
    model_name: str,
    api_key: str,
    base_url: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    frequency_penalty: float,
    presence_penalty: float,
    seed: int,
    tools_limit: int,
    get_enabled_tools,
    build_tool_prompt,
    run_auto_tools_and_status,
    get_tools_registry,
) -> str:
    """Run the unified inference loop to completion and return the final content (non-streaming mode)."""
    # Log all parameters for non-streaming mode as well
    api_params = {
        "model": model_name,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "streaming": False,
    }
    if seed is not None:
        api_params["seed"] = seed
    print(f"[OpenAI API Call - Non-streaming] Parameters: {api_params}")

    final_content: str = ""
    async for event in inference_loop(
        base_messages,
        conversation_id=conversation_id,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        seed=seed,
        tools_limit=tools_limit,
        get_enabled_tools=get_enabled_tools,
        build_tool_prompt=build_tool_prompt,
        run_auto_tools_and_status=run_auto_tools_and_status,
        get_tools_registry=get_tools_registry,
    ):
        et = event.get("type")
        if et == "chunk":
            final_content += event.get("content", "")
        elif et == "complete":
            final_content = event.get("content", final_content)
            break
        elif et == "error":
            raise Exception(event.get("message") or "Inference error")
    return final_content


# Global chat service instance
chat_service = ChatService()
