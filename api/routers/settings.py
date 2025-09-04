"""
Settings API router for Ghostpad.

Handles OpenAI settings, system prompt settings, sampling parameters, 
user description, and prompt editing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from services.ai_service import ai_service
from services.system_prompt_service import system_prompt_service

router = APIRouter()

# Pydantic models
class OpenAISettings(BaseModel):
    base_url: str
    api_key: str
    model_name: str
    streaming_enabled: bool = True

class OpenAISettingsResponse(BaseModel):
    base_url: str
    api_key: str
    model_name: str
    streaming_enabled: bool

class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    model_info: Dict[str, Any] = None

class SystemPromptItem(BaseModel):
    title: str
    content: str

class SystemPromptSettings(BaseModel):
    system_prompts: List[SystemPromptItem] = []
    include_datetime: bool = False
    enabled: bool = True
    thinking_mode: str = 'default'

class SystemPromptResponse(BaseModel):
    system_prompts: List[SystemPromptItem] = []
    include_datetime: bool
    enabled: bool
    thinking_mode: str

class SamplingSettings(BaseModel):
    temperature: float = 1.0
    top_p: float = 1.0
    max_tokens: int = 1000
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    seed: Optional[int] = None
    top_k: Optional[int] = None

class SamplingResponse(BaseModel):
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float
    presence_penalty: float
    seed: Optional[int] = None
    top_k: Optional[int] = None

class UserDescriptionSettings(BaseModel):
    user_description: str = None
    user_name: str = "User"

class UserDescriptionResponse(BaseModel):
    user_description: str = None
    user_name: str = "User"

class PromptEditRequest(BaseModel):
    draft: str
    instructions: str

class PromptEditResponse(BaseModel):
    edited: str


# OpenAI Settings endpoints
@router.get("/api/settings/openai", response_model=OpenAISettingsResponse)
async def get_openai_settings():
    """Get OpenAI API settings"""
    try:
        settings = await ai_service.get_openai_settings()
        return OpenAISettingsResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OpenAI settings: {str(e)}")


@router.post("/api/settings/openai", response_model=OpenAISettingsResponse)
async def save_openai_settings(settings: OpenAISettings):
    """Save OpenAI API settings"""
    try:
        saved_settings = await ai_service.save_openai_settings(
            base_url=settings.base_url,
            api_key=settings.api_key,
            model_name=settings.model_name,
            streaming_enabled=settings.streaming_enabled
        )
        return OpenAISettingsResponse(**saved_settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save OpenAI settings: {str(e)}")


@router.post("/api/settings/openai/test", response_model=ConnectionTestResponse)
async def test_openai_connection(settings: OpenAISettings):
    """Test connection to OpenAI API and return available models"""
    try:
        result = await ai_service.test_connection(settings.base_url, settings.api_key)
        return ConnectionTestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# System Prompt endpoints
@router.get("/api/settings/system-prompt", response_model=SystemPromptResponse)
async def get_system_prompt_settings():
    """Get system prompt settings"""
    try:
        settings = await system_prompt_service.get_system_prompt_settings()
        return SystemPromptResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system prompt settings: {str(e)}")


@router.post("/api/settings/system-prompt", response_model=SystemPromptResponse)
async def save_system_prompt_settings(settings: SystemPromptSettings):
    """Save system prompt settings"""
    try:
        saved_settings = await system_prompt_service.save_system_prompt_settings(
            system_prompts=settings.system_prompts,
            include_datetime=settings.include_datetime,
            enabled=settings.enabled,
            thinking_mode=settings.thinking_mode
        )
        return SystemPromptResponse(**saved_settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save system prompt settings: {str(e)}")


# User Description endpoints
@router.get("/api/settings/user-description", response_model=UserDescriptionResponse)
async def get_user_description_settings():
    """Get user description settings"""
    try:
        settings = await system_prompt_service.get_user_description_settings()
        return UserDescriptionResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user description settings: {str(e)}")


@router.post("/api/settings/user-description", response_model=UserDescriptionResponse)
async def save_user_description_settings(settings: UserDescriptionSettings):
    """Save user description settings"""
    try:
        saved_settings = await system_prompt_service.save_user_description_settings(
            user_description=settings.user_description or "",
            user_name=settings.user_name or "User"
        )
        return UserDescriptionResponse(**saved_settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user description settings: {str(e)}")


# Sampling Parameters endpoints
@router.get("/api/settings/sampling", response_model=SamplingResponse)
async def get_sampling_settings():
    """Get sampling parameters"""
    try:
        settings = await ai_service.get_sampling_settings()
        return SamplingResponse(**settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sampling settings: {str(e)}")


@router.post("/api/settings/sampling", response_model=SamplingResponse)
async def save_sampling_settings(settings: SamplingSettings):
    """Save sampling parameters"""
    try:
        saved_settings = await ai_service.save_sampling_settings(
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_tokens=settings.max_tokens,
            frequency_penalty=settings.frequency_penalty,
            presence_penalty=settings.presence_penalty,
            seed=settings.seed,
            top_k=settings.top_k
        )
        return SamplingResponse(**saved_settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save sampling settings: {str(e)}")


# Prompt editing endpoint
@router.post("/api/prompt/edit", response_model=PromptEditResponse)
async def edit_prompt(data: PromptEditRequest):
    """Edit a prompt using the configured OpenAI model"""
    try:
        edited = await ai_service.edit_prompt(data.draft, data.instructions)
        return PromptEditResponse(edited=edited)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edit failed: {str(e)}")