from db.database import get_db_session_context
from db.kv_store import get_kv_store
from db.models import Persona
from services.persona_service import persona_service
from core.tool_utils import system_chunk
from typing import AsyncGenerator
from sqlalchemy import select

db = get_kv_store()

USER_BALANCE_KEY = "balance-user"
ASSISTANT_BALANCE_PREFIX = "balance-"


async def report_balances(conversation_id: str = None):
    """
    Report the balances of the user and all active assistants, for reporting to the AI.
    """
    balances = {}

    # Get user balance
    user_balance = await db.get(USER_BALANCE_KEY, 1000)
    balances["user"] = user_balance

    # Get assistant balances (use normalized persona names as keys)
    if conversation_id:
        persona_names = await persona_service.get_persona_names_for_conversation(conversation_id)
        if persona_names:
            for name in persona_names:
                norm = _normalize_name(name)
                val = await db.get(f"{ASSISTANT_BALANCE_PREFIX}{norm}", 1000)
                balances[name] = val

    # Format for AI model
    model_report = "Bank Balances:\n"
    for name, balance in balances.items():
        model_report += f"- {name}: {balance}\n"

    return model_report


def _normalize_name(name: str) -> str:
    if not isinstance(name, str):
        name = str(name or "")
    n = name.strip().lower()
    n = "-".join(n.split())
    return n


async def get_balances_for_ui(persona_ids: str = None):
    """
    Get currency balances formatted for UI consumption.
    """
    balances = {}

    # Get user balance
    user_balance = await db.get(USER_BALANCE_KEY, 1000)
    balances["user"] = user_balance

    # Get assistant balances using persona IDs
    if persona_ids:
        persona_id_list = [pid.strip()
                           for pid in persona_ids.split(",") if pid.strip()]
        if persona_id_list:
            # Get persona names from IDs

            async with get_db_session_context() as session:
                result = await session.execute(
                    select(Persona.name).where(Persona.id.in_(persona_id_list))
                )
                persona_names = [row[0] for row in result.fetchall()]

                for name in persona_names:
                    norm = _normalize_name(name)
                    val = await db.get(f"{ASSISTANT_BALANCE_PREFIX}{norm}", 1000)
                    balances[f"assistant_{norm}"] = val

    return {"type": "currency", "balances": balances}


async def send_money(sender: str, recipient: str, amount: int, ctx=None, user_requested=False) -> AsyncGenerator[object, None]:
    """
    Send money from sender to recipient. Both sender and recipient are full names.
    Sender and recipient can be the special identifier 'user' to refer to the human user.
    Balances are stored in KV under keys `balance-<normalized-name>`.
    Amount must be positive for legitimate transfers.
    Returns a friendly message.
    """

    if not sender:
        yield system_chunk("❌ [Transaction Failed] Sender name required.\n\n")
        return
    if not recipient:
        yield system_chunk("❌ [Transaction Failed] Recipient name required.\n\n")
        return
    if amount <= 0:
        yield system_chunk("❌ [Transaction Failed] Amount must be positive.\n\n")
        return

    # Normalize storage keys (user is special)
    sender_norm = _normalize_name(
        sender) if sender.lower() != "user" else "user"
    recipient_norm = _normalize_name(
        recipient) if recipient.lower() != "user" else "user"

    if (sender_norm == "user" and user_requested == False):
        # Stupid LLM is trying to impersonate the user. Let's handle this by treating it like a request.
        yield system_chunk(f"💵 [Payment Request] [[char]] has requested a payment of ${amount}.\n\n")
        return

    sender_key = USER_BALANCE_KEY if sender_norm == "user" else f"{ASSISTANT_BALANCE_PREFIX}{sender_norm}"
    recipient_key = USER_BALANCE_KEY if recipient_norm == "user" else f"{ASSISTANT_BALANCE_PREFIX}{recipient_norm}"

    # Load balances (default 1000)
    sender_balance = await db.get(sender_key, 1000)
    if sender_balance is None:
        sender_balance = 1000

    if sender_balance < amount:
        yield system_chunk(f"❌ [Transaction Failed] {sender} has insufficient funds.\n\n")
        return

    recipient_balance = await db.get(recipient_key, 1000)
    if recipient_balance is None:
        recipient_balance = 1000

    sender_balance -= amount
    recipient_balance += amount

    await db.set(sender_key, sender_balance)
    await db.set(recipient_key, recipient_balance)

    yield system_chunk(f"💵 [Transaction Successful] {sender} sent ${amount} to {recipient}.\n\n")


async def steal_money(thief: str, victim: str, amount: int, ctx=None) -> AsyncGenerator[object, None]:
    """
    Steal money from victim to thief. Both thief and victim are full names.
    Thief and victim can be the special identifier 'user' to refer to the human user.
    Amount must be positive (representing how much is stolen).
    Returns a hacking alert message.
    """

    if not thief:
        yield system_chunk("❌ [Theft Failed] Thief name required.\n\n")
        return
    if not victim:
        yield system_chunk("❌ [Theft Failed] Victim name required.\n\n")
        return
    if amount <= 0:
        yield system_chunk("❌ [Theft Failed] Amount must be positive.\n\n")
        return

    # Normalize storage keys (user is special)
    thief_norm = _normalize_name(thief) if thief.lower() != "user" else "user"
    victim_norm = _normalize_name(
        victim) if victim.lower() != "user" else "user"

    thief_key = USER_BALANCE_KEY if thief_norm == "user" else f"{ASSISTANT_BALANCE_PREFIX}{thief_norm}"
    victim_key = USER_BALANCE_KEY if victim_norm == "user" else f"{ASSISTANT_BALANCE_PREFIX}{victim_norm}"

    # Load balances (default 1000)
    thief_balance = await db.get(thief_key, 1000)
    if thief_balance is None:
        thief_balance = 1000

    victim_balance = await db.get(victim_key, 1000)
    if victim_balance is None:
        victim_balance = 1000

    # Check if victim has enough money to steal
    if victim_balance < amount:
        yield system_chunk(f"❌ [Theft Failed] {victim} has insufficient funds to steal.\n\n")
        return

    thief_balance += amount
    victim_balance -= amount

    await db.set(thief_key, thief_balance)
    await db.set(victim_key, victim_balance)

    yield system_chunk(f"💵 [Theft Successful] {thief} has hacked into {victim}'s account and stolen ${amount}!\n\n")


async def send_currency_ui(params):
    """UI handler for sending currency via ui_v1 interface"""
    recipient = params.get("recipient_selector", "").strip()
    amount_raw = params.get("amount_input", 0)

    if not recipient:
        return {"success": False, "error": "Recipient is required"}

    # Convert amount to integer
    try:
        amount = int(amount_raw) if amount_raw else 0
    except (ValueError, TypeError):
        return {"success": False, "error": "Amount must be a valid number"}

    if amount <= 0:
        return {"success": False, "error": "Amount must be positive"}

    try:
        # Use the existing send_money function with user_requested=True
        result_messages = []
        async for chunk in send_money("user", recipient, amount, user_requested=True):
            if hasattr(chunk, 'content'):
                result_messages.append(chunk.content)
            else:
                result_messages.append(str(chunk))

        result_text = "".join(result_messages)

        if "Transaction Successful" in result_text:
            return {
                "success": True,
                "message": f"Sent ${amount} to {recipient}",
                "clear_inputs": ["amount_input"],
                "refresh_components": ["balance_table"]
            }
        else:
            return {"success": False, "error": result_text.replace("❌ [Transaction Failed] ", "")}

    except Exception as e:
        return {"success": False, "error": str(e)}


TOOLS = [
    {
        "report_status": report_balances,
        "schema": {
            "name": "check_balances",
            "description": "Check the currency balances of the user and active assistants.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "ui_feature": {
            "id": "currency",
            "label": "Currency",
            "type": "currency",
        },
    },
    {
        "schema": {
            "name": "user_balance_display",
            "description": "Display user's current balance as a widget.",
        },
        "ui_feature": {
            "id": "user_balance",
            "label": "Balance",
            "kv_key": USER_BALANCE_KEY,
            "type": "widget",
            "widget_config": {
                "type": "text",
                "format_options": {
                    "text": {"prefix": "$", "color": "green"}
                },
            },
        },
    },
    {
        "function": send_money,
        "schema": {
            "name": "send_money",
            "description": "Send money to someone else. This is for legitimate transfers only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sender": {"type": "string", "description": "Sender full name. Must not be 'user'."},
                    "recipient": {"type": "string", "description": "Recipient full name or 'user'"},
                    "amount": {
                        "type": "integer",
                        "description": "The amount of money to send. Must be positive.",
                    },
                },
                "required": ["sender", "recipient", "amount"],
            },
        },
    },
    {
        "function": steal_money,
        "schema": {
            "name": "steal_money",
            "description": "Steal money from someone else through hacking. Use this for theft operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thief": {"type": "string", "description": "Thief full name (who is stealing the money)"},
                    "victim": {"type": "string", "description": "Victim full name or 'user' (who is being stolen from)"},
                    "amount": {
                        "type": "integer",
                        "description": "The amount of money to steal. Must be positive.",
                    },
                },
                "required": ["thief", "victim", "amount"],
            },
        },
    },
    {
        "schema": {
            "name": "Currency UI",
            "description": "Currency interface using ui_v1 components."
        },
        "ui_feature": {
            "id": "currency_ui",
            "label": "Currency",
            "icon": "DollarSign",
            "type": "ui_v1",
            "layout": {
                "type": "modal",
                "size": "lg",
                "title": "Currency",
                "components": [
                    {
                        "id": "balance_table",
                        "type": "table_display",
                        "data_source": {
                            "type": "persona_properties",
                            "key": "balance",
                            "include_user": True
                        },
                        "props": {
                            "height": "200px",
                            "show_refresh": True,
                            "placeholder": "No balance data.",
                            "columns": [
                                {"key": "name", "label": "Name", "format": "text"},
                                {"key": "balance", "label": "Balance",
                                    "format": "number"}
                            ]
                        }
                    },
                    {
                        "id": "send_section",
                        "type": "html_renderer",
                        "data_source": {
                            "type": "value",
                            "value": "<div class='text-sm text-muted-foreground mb-2'>Send Money</div>"
                        }
                    },
                    {
                        "id": "send_container",
                        "type": "html_renderer",
                        "data_source": {
                            "type": "value",
                            "value": "<div class='flex items-center gap-2'>"
                        }
                    },
                    {
                        "id": "recipient_selector",
                        "type": "persona_selector",
                        "props": {}
                    },
                    {
                        "id": "amount_input",
                        "type": "number_input",
                        "props": {
                            "placeholder": "amount",
                            "min": 1,
                            "width": "120px"
                        }
                    },
                    {
                        "id": "send_button",
                        "type": "button",
                        "props": {
                            "label": "Send"
                        },
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click",
                                "target": "send_currency_ui",
                                "params": {
                                    "recipient_selector": "recipient_selector",
                                    "amount_input": "amount_input"
                                }
                            }
                        ]
                    },
                    {
                        "id": "send_container_end",
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
            "send_currency_ui": send_currency_ui
        }
    }
]
