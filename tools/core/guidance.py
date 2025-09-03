from db.kv_store import get_kv_store
import traceback

KEY = "guidance_next_response"

db = get_kv_store()


async def set_guidance(value: str):
    """Set guidance text to be injected into the next response."""
    print(f"Setting guidance to: {value}")
    await db.set(KEY, value or "")
    return


async def check_guidance():
    """Read-only check for guidance.
    This function is intended to be used as a `report_status` function so the
    model can be given the current guidance in their status display.
    The actual clearing/consuming should be done in a cleanup function after
    the full response cycle completes.
    """
    guidance = await db.get(KEY, "") or ""
    if not guidance:
        return ""
    return "You MUST follow the below instructions from the system administrators:\n```\n" + str(guidance) + "\n```"


async def consume_guidance():
    """Clear the pending guidance. Intended to be called once the whole
    response is finished (cleanup function).
    """
    try:
        print("Consuming guidance and clearing KEY")
        await db.set(KEY, "")
    except Exception:
        traceback.print_exc()
    return ""


async def save_guidance_ui(params):
    """UI handler for saving guidance via ui_v1 interface"""
    guidance_text = params.get("guidance_textarea", "").strip()

    try:
        await db.set(KEY, guidance_text)
        return {"success": True, "message": "Guidance saved"}

    except Exception as e:
        return {"success": False, "error": str(e)}


TOOLS = [
    {
        "report_status": check_guidance,
        "cleanup_function": consume_guidance,
        "schema": {
            "name": "check_guidance",
            "description": "Check for guidance for the next response; if present, inject it (read-only).",
        },
        "ui_feature": {
            "id": "guidance",
            "label": "Guidance",
            "kv_key": KEY,
            "type": "modal_textarea",
        },
    },
    {
        "function": set_guidance,
        "one_time": True,
        "schema": {
            "name": "set_guidance",
            "description": "Set guidance text to be injected into the next response. Use this tool to set guidelines on how to respond to the user's request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "string",
                        "description": "The guidance text",
                    }
                },
                "required": ["value"],
            },
        },
    },
    {
        "schema": {
            "name": "Guidance UI v1",
            "description": "Guidance interface using ui_v1 components."
        },
        "ui_feature": {
            "id": "guidance_ui",
            "label": "Guidance",
            "icon": "Waypoints",
            "type": "ui_v1",
            "layout": {
                "type": "modal",
                "size": "lg",
                "title": "Guidance",
                "components": [
                    {
                        "id": "guidance_textarea",
                        "type": "textarea_input",
                        "data_source": {
                            "type": "kv_store",
                            "key": KEY
                        },
                        "props": {
                            "placeholder": "Enter guidance for the next response...",
                            "min_height": "112px"
                        }
                    },
                    {
                        "id": "button_row",
                        "type": "html_renderer",
                        "data_source": {
                            "type": "value",
                            "value": "<div class='flex items-center gap-2 mt-4'>"
                        }
                    },
                    {
                        "id": "save_button",
                        "type": "button",
                        "props": {
                            "label": "Save Guidance"
                        },
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "save_guidance_ui",
                                "params": {
                                    "guidance_textarea": "guidance_textarea"
                                }
                            }
                        ]
                    },
                    {
                        "id": "library_manager",
                        "type": "library_manager",
                        "data_source": {
                            "type": "library",
                            "library_type": "guidance",
                            "target_component_id": "guidance_textarea"
                        },
                        "props": {
                            "placeholder": "No saved guidance snippets."
                        }
                    },
                    {
                        "id": "button_row_end",
                        "type": "html_renderer",
                        "data_source": {
                            "type": "value",
                            "value": "</div>"
                        }
                    }
                ]
            }
        },
        "ui_handlers": {
            "save_guidance_ui": save_guidance_ui
        }
    }
]
