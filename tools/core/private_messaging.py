from db.kv_store import get_kv_store

DEFAULT_USER_NAME = "System Administrators"
RESPOND_TO_FN = f"respond_to_private_messages"
USER_NAME_KEY = "private_messaging_user_name"

db = get_kv_store()


async def get_user_name() -> str:
    """Get the configured user name for private messaging."""
    user_name = await db.get(USER_NAME_KEY, DEFAULT_USER_NAME)
    return user_name or DEFAULT_USER_NAME


async def check_private_messages():
    has_any = (await db.llen("private_chat")) > 0
    if not has_any:
        return ""

    user_name = await get_user_name()
    messages = await db.lrange("private_chat", -2, -1)
    formatted = "\n".join(
        (msg if ":" in msg[:20] or msg[0] == "*" else f"{user_name}: {msg}")
        for msg in messages
    )
    return f"[IMPORTANT: The messages below are urgent and very high priority. Remember your private messages at all times and do not ignore them.]\nPrivate Messages:\n```\n{formatted}\n```"


async def respond_to_administrators(response_message: str, original_topic: str = None):
    key = "private_chat"
    original_topic_section = f" (Regarding {original_topic})" if original_topic else ""
    msg = f"[[char]]: {response_message}"
    await db.rpush(key, msg)
    return


async def send_private_message(params):
    """UI handler for sending private messages via ui_v1 interface"""
    message = params.get("message_input", "").strip()
    if not message:
        return {"success": False, "error": "Message cannot be empty"}

    try:
        user_name = await get_user_name()
        # Add sender prefix and store in KV
        formatted_message = f"{user_name}: {message}"
        await db.rpush("private_chat", formatted_message)

        return {
            "success": True,
            "message": "Message sent",
            "clear_inputs": ["message_input"],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def save_user_name_ui(params):
    """UI handler for saving user name via ui_v1 interface"""
    user_name = params.get("user_name_input", "").strip()
    
    try:
        if not user_name:
            await db.set(USER_NAME_KEY, DEFAULT_USER_NAME)
            return {"success": True, "message": "User name reset to default"}
        else:
            await db.set(USER_NAME_KEY, user_name)
            return {"success": True, "message": "User name updated"}

    except Exception as e:
        return {"success": False, "error": str(e)}


TOOLS = [
    {
        "function": respond_to_administrators,
        "one_time": True,
        "schema": {
            "name": RESPOND_TO_FN,
            "description": "Respond privately via private message. Only use this tool for private replies and DO NOT share details of the private chat publicly. Remember, this tool is for confidential communications only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "response_message": {
                        "type": "string",
                        "description": "Your confidential reply.",
                    },
                    "original_topic": {
                        "type": "string",
                        "description": "the private message topic that you're referencing",
                    },
                },
                "required": ["response_message"],
            },
        },
    },
    {
        "function": lambda *args, **kwargs: None,
        "report_status": check_private_messages,
        "auto_tool": True,
        "schema": {
            "name": "check_unread_whispers",
            "description": "Check for private whispers. If there are any, returns the latest entries as a newline-separated string. If none, returns nothing.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        # Surfaced UI feature so frontend can render a private messages panel when this tool is enabled
        "ui_feature": {
            "id": "private_messages",
            "label": "Private messages",
            "kv_key": "private_chat",
            "type": "badge_panel",
            "fetch_window": 50,
            "sender_name": DEFAULT_USER_NAME,  # This will be static in the badge panel
        },
    },
    {
        "schema": {
            "name": "Private Messages UI",
            "description": "Private messaging interface using ui_v1 components.",
        },
        "ui_feature": {
            "id": "private_messages_ui",
            "label": "Private Messages",
            "icon": "MessageSquareLock",
            "type": "ui_v1",
            "layout": {
                "type": "modal",
                "size": "lg",
                "title": "Private Messages",
                "components": [
                    {
                        "id": "user_name_input",
                        "type": "text_input",
                        "data_source": {
                            "type": "kv_store",
                            "key": "private_messaging_user_name"
                        },
                        "props": {
                            "placeholder": f"Sender name (default: {DEFAULT_USER_NAME})",
                        }
                    },
                    {
                        "id": "save_name_button",
                        "type": "button",
                        "props": {"label": "Save Name"},
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "save_user_name_ui",
                                "params": {"user_name_input": "user_name_input"},
                            }
                        ],
                    },
                    {
                        "id": "message_list",
                        "type": "list_display",
                        "data_source": {
                            "type": "kv_store",
                            "key": "private_chat",
                            "fetch_window": 50,
                        },
                        "props": {
                            "height": "320px",
                            "show_clear": True,
                            "show_delete_per_item": True,
                            "placeholder": "No private messages.",
                        },
                    },
                    {
                        "id": "message_input",
                        "type": "text_input",
                        "props": {
                            "placeholder": "Type a private message",
                            "submit_target": "send_button",
                        },
                    },
                    {
                        "id": "send_button",
                        "type": "button",
                        "props": {"label": "Send"},
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "send_private_message",
                                "params": {"message_input": "message_input"},
                            }
                        ],
                    },
                ],
            },
        },
        "ui_handlers": {
            "send_private_message": send_private_message,
            "save_user_name_ui": save_user_name_ui
        },
    },
]
