from utils.tool_utils import create_system_message_in_conversation, system_chunk
from typing import AsyncGenerator
from services.kv_store_service import kv_store

DEFAULT_OUTFIT = "Casual T-shirt and Jeans"


def get_clothing_key(conversation_id: str) -> str:
    """Get the KV store key for clothing, scoped to a conversation"""
    return f"equipped_clothing_{conversation_id}"


async def get_equipped_clothing(conversation_id: str = None):
    """Get assistant's currently equipped clothing."""
    if not conversation_id:
        return f"[[char]] is wearing: {DEFAULT_OUTFIT}"
    
    key = get_clothing_key(conversation_id)
    # Initialize with default clothing if none exists
    equipped = await kv_store.get(key, None)
    if equipped is None:
        await kv_store.set(key, DEFAULT_OUTFIT)
        equipped = DEFAULT_OUTFIT
    return f"[[char]] is wearing: {equipped}"


async def wear_clothing(item_name: str, metadata=None) -> AsyncGenerator[object, None]:
    if not isinstance(item_name, str) or not item_name.strip():
        return

    conversation_id = metadata.get("conversation_id") if metadata else None
    if not conversation_id:
        yield system_chunk("⚠️ *Cannot change clothing without conversation context.*\n\n")
        return
        
    key = get_clothing_key(conversation_id)
    current_equipped = await kv_store.get(key, DEFAULT_OUTFIT)

    if current_equipped == item_name:
        yield system_chunk(f"👕 *[[char]] is already wearing '{item_name}'!*\n\n")
        return

    yield system_chunk(f"👔 *Getting ready to change into '{item_name}'...* \n\n")
    yield system_chunk("**Rustle rustle...**\n\n")

    await kv_store.set(key, item_name)

    yield system_chunk(f"✨ *Perfect! [[char]] is now wearing '{item_name}'!*\n\n")


async def save_clothing_ui(params, metadata=None):
    """UI handler for saving clothing via ui_v1 interface"""
    clothing_text = params.get("clothing_textarea", "").strip()
    conversation_id = metadata.get("conversation_id") if metadata else None
    
    if not conversation_id:
        return {"success": False, "error": "Cannot save clothing without conversation context"}
    
    key = get_clothing_key(conversation_id)

    new_clothing = clothing_text or DEFAULT_OUTFIT

    await create_system_message_in_conversation(f"👕 *poof!* [[user]] has changed [[char]]'s outfit to: {new_clothing}", conversation_id)

    await kv_store.set(key, new_clothing)

    try:
        if not clothing_text:
            return {"success": True, "message": "Clothing reset to default"}
        else:
            return {"success": True, "message": "Clothing updated"}

    except Exception as e:
        return {"success": False, "error": str(e)}

TOOLS = [
    {
        "report_status": get_equipped_clothing,
        "auto_tool": True,
        "schema": {
            "name": "get_equipped_clothing",
            "description": "Get assistant's currently equipped clothing for this conversation.",
        },
    },
    {
        "function": wear_clothing,
        "schema": {
            "name": "wear_clothing",
            "description": "Equip a clothing item with streaming text updates. Scoped to current conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name of the clothing item to wear",
                    }
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "schema": {
            "name": "Clothing UI v1",
            "description": "Clothing interface using ui_v1 components for user control."
        },
        "ui_feature": {
            "id": "clothing_ui",
            "label": "Clothing",
            "icon": "Shirt",
            "type": "ui_v1",
            "layout": {
                "type": "modal",
                "size": "md",
                "title": "Set Character Clothing",
                "components": [
                    {
                        "id": "clothing_textarea",
                        "type": "textarea_input",
                        "data_source": {
                            "type": "kv_store",
                            "key": "equipped_clothing_{conversation_id}"
                        },
                        "props": {
                            "placeholder": "Enter what the character is wearing...",
                            "min_height": "100px",
                            "show_ai_edit": True,
                            "ai_edit_label": "Edit Character Clothing"
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
                            "label": "Save Clothing"
                        },
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "save_clothing_ui",
                                "params": {
                                    "clothing_textarea": "clothing_textarea"
                                }
                            }
                        ]
                    },
                    {
                        "id": "reset_button",
                        "type": "button",
                        "props": {
                            "label": "Reset to Default",
                            "variant": "secondary"
                        },
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "save_clothing_ui",
                                "params": {
                                    "clothing_textarea": ""
                                }
                            }
                        ]
                    },
                    {
                        "id": "library_manager",
                        "type": "library_manager",
                        "data_source": {
                            "type": "library",
                            "library_type": "clothing",
                            "target_component_id": "clothing_textarea"
                        },
                        "props": {
                            "placeholder": "No saved clothing templates."
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
            "save_clothing_ui": save_clothing_ui
        }
    }
]
