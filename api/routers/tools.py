"""
Tools API router for Ghostpad.

Handles tool management, enabling/disabling, and UI feature extraction.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from services.tool_service import tool_service


router = APIRouter()


# Pydantic models
class ToolToggleRequest(BaseModel):
    enabled: bool


class ToolSubmitRequest(BaseModel):
    handler: str
    params: Dict[str, Any]


@router.get("/api/tools")
async def list_tools():
    """List discovered tools with their enabled state and schemas."""
    try:
        tools = tool_service.get_tools_list()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get("/api/tools/features")
async def list_tool_features():
    """List UI features derived from enabled tools."""
    try:
        features = await tool_service.get_tool_features()
        return {"features": features}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list tool features: {str(e)}"
        )


@router.get("/api/tools/by-file")
async def list_tools_by_file():
    """List tools grouped by file with file-level metadata."""
    try:
        files = tool_service.get_tools_by_file()
        return {"files": files}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list tools by file: {str(e)}"
        )


@router.post("/api/tools/file/{module_name}/toggle")
async def toggle_file_tools(module_name: str, data: ToolToggleRequest):
    """Enable or disable all tools in a file."""
    try:
        success = await tool_service.toggle_file_tools(module_name, data.enabled)
        if not success:
            raise HTTPException(
                status_code=404, detail="Module not found or has no tools"
            )

        return {"module": module_name, "enabled": data.enabled}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle file tools: {str(e)}"
        )


@router.post("/api/tools/{tool_id}/toggle")
async def toggle_tool(tool_id: str, data: ToolToggleRequest):
    """Enable or disable a tool by id, and persist the selection."""
    try:
        success = await tool_service.toggle_tool(tool_id, data.enabled)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"id": tool_id, "enabled": data.enabled}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle tool: {str(e)}")


@router.post("/api/tool_submit")
async def submit_tool_handler(data: ToolSubmitRequest):
    """Execute a UI handler function from enabled tools"""
    try:
        conversation_id = data.params.get("conversation_id")
        result = await tool_service.execute_ui_handler(
            data.handler, data.params, conversation_id
        )
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Handler execution failed: {str(e)}")
