"""
Chat API router for Ghostpad.

Handles chat message creation, streaming, regeneration, and title generation.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.chat_service import chat_service
from services.conversation_service import conversation_service
from services.sse_service import sse_service
from services.suggestion_service import suggestion_service
from utils.constants import MIME_EVENT_STREAM

router = APIRouter()


# Pydantic models
class ChatMessageCreate(BaseModel):
    content: str
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    content: str
    role: str
    created_at: str
    conversation_id: str
    user_message_id: Optional[int] = None  # ID of the user message that triggered this response


class GenerateTitleRequest(BaseModel):
    conversation_id: str
    user_message: str
    assistant_message: str


class GenerateTitleResponse(BaseModel):
    title: str


class RegenerateRequest(BaseModel):
    conversation_id: str
    message_id_to_replace: int
    user_prompt: str
    use_streaming: bool = False


class RegenerateResponse(BaseModel):
    message: ChatMessageResponse


class PromptSuggestionRequest(BaseModel):
    conversation_id: Optional[str] = None

sse_headers = sse_service.get_sse_headers()

@router.post("/api/chat", response_model=ChatMessageResponse)
async def send_chat_message(data: ChatMessageCreate):
    """Send a message and get OpenAI response, persisting both"""
    try:
        # Create user message
        user_result = await chat_service.create_user_message(
            content=data.content, conversation_id=data.conversation_id
        )

        # Generate response
        response = await chat_service.generate_response(
            conversation_id=user_result["conversation_id"],
        )

        # Include the user message ID in the response
        response["user_message_id"] = user_result["message"]["id"]

        return ChatMessageResponse(**response)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/api/chat/stream")
async def stream_chat_message(data: ChatMessageCreate):
    """Stream a chat message response using SSE"""

    async def generate_stream():
        try:
            conversation_id = data.conversation_id

            # Create user message only if content is not empty
            if data.content.strip():
                user_result = await chat_service.create_user_message(
                    content=data.content, conversation_id=data.conversation_id
                )

                conversation_id = user_result["conversation_id"]

                # Send user message to client using SSE service
                yield sse_service.format_custom_event(
                    "user_message", {"message": user_result["message"]}
                )

            # Prepare conversation messages using ChatService
            base_messages = await chat_service.prepare_conversation_messages(
                conversation_id
            )

            generator = chat_service.get_streaming_generator(
                conversation_id, base_messages
            )

            # Stream events using SSE service for consistent formatting
            async for sse_event in sse_service.stream_service_events(
                generator,
                error_prefix="Chat error",
            ):
                yield sse_event

        except Exception as e:
            yield f"data: {json.dumps({'error': f'Chat error: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_stream(), media_type=MIME_EVENT_STREAM, headers=sse_headers
    )


@router.post("/api/chat/regenerate")
async def regenerate_message(data: RegenerateRequest):
    """Regenerate an assistant's response"""
    try:
        if data.use_streaming:
            # Prepare regeneration messages using ChatService
            messages_for_api = await chat_service.prepare_regeneration_messages(
                data.conversation_id, data.message_id_to_replace
            )

            # Use unified streaming generator for regeneration
            async def regenerate_stream():
                try:
                    # Stream events using SSE service for consistent formatting
                    generator = chat_service.get_streaming_generator(
                        conversation_id=data.conversation_id,
                        messages_for_api=messages_for_api,
                        is_regeneration=True,
                        message_id_to_replace=data.message_id_to_replace,
                    )
                    async for sse_event in sse_service.stream_service_events(
                        generator, error_prefix="Regeneration error"
                    ):
                        yield sse_event
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Regeneration error: {str(e)}'})}\n\n"

            return StreamingResponse(
                regenerate_stream(),
                media_type=MIME_EVENT_STREAM,
                headers=sse_headers,
            )
        else:
            # Regular regeneration (non-streaming)
            result = await chat_service.regenerate_message(
                conversation_id=data.conversation_id,
                message_id_to_replace=data.message_id_to_replace,
            )

            return RegenerateResponse(message=ChatMessageResponse(**result["message"]))

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.post("/api/chat/generate-title", response_model=GenerateTitleResponse)
async def generate_conversation_title(data: GenerateTitleRequest):
    """Generate a concise title for a conversation based on the first exchange"""
    try:
        title = await conversation_service.generate_title(
            conversation_id=data.conversation_id,
            user_message=data.user_message,
            assistant_message=data.assistant_message,
        )

        return GenerateTitleResponse(title=title)

    except Exception:
        # If title generation fails, return a default title
        return GenerateTitleResponse(title="New Chat")


@router.post("/api/chat/suggest-prompt")
async def suggest_prompt(data: PromptSuggestionRequest):
    """Generate a prompt suggestion based on conversation context"""

    # Use SuggestionService for all the complex logic
    async def generate_suggestion_stream():
        async for sse_event in sse_service.stream_service_events(
            suggestion_service.generate_prompt_suggestion(data.conversation_id),
            error_prefix="Suggestion error",
        ):
            yield sse_event

    return StreamingResponse(
        generate_suggestion_stream(),
        media_type=MIME_EVENT_STREAM,
        headers=sse_headers()
    )
