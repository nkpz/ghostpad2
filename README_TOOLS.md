# Ghostpad Tools API Reference

The Ghostpad Tools API provides a comprehensive system for creating intelligent tools that integrate with LLM conversations. This API extends standard LLM function calling with advanced features including auto-execution, real-time streaming, conditional availability, rich UI components, and lifecycle management.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Tool Creation](#basic-tool-creation)
3. [Tool Configuration Features](#tool-configuration-features)
4. [Streaming Tools](#streaming-tools)
5. [UI Tools](#ui-tools)
6. [Service Integration](#service-integration)
7. [Error Handling](#error-handling)
8. [Complete Examples](#complete-examples)

---

## Getting Started

### Tool Registration

All tools must be defined in Python files within the `tools/` directory using the following structure:

```python
# tools/my_tool.py
TOOLS: List[ToolDefinition] = [
    {
        # Tool definition here
    }
]
```

### Tool Discovery

The system automatically discovers tools by:
1. Scanning all `.py` files in `tools/` and subdirectories
2. Importing each module and extracting the `TOOLS` list
3. Registering each tool with a unique ID: `{module_name}.{tool_name}`
4. Building a registry with metadata and capability flags

---

## Basic Tool Creation

### Core Types

#### ToolDefinition

```python
class ToolDefinition(TypedDict):
    function: Optional[Callable[..., Any]]              # Tool execution function
    schema: ToolSchema                                  # OpenAI-compatible schema
    auto_tool: Optional[bool]                          # Auto-execute flag
    one_time: Optional[bool]                           # Single-use flag
    condition: Optional[Callable[[], Union[bool, Awaitable[bool]]]]  # Availability condition
    report_status: Optional[Callable[..., Union[str, Awaitable[str]]]]  # Status reporter
    cleanup_function: Optional[Callable[[], Union[None, Awaitable[None]]]]  # Cleanup handler
    ui_feature: Optional[UIFeatureConfig]              # UI component config
    ui_handlers: Optional[Dict[str, UIHandlerFunction]]  # UI event handlers
```

#### ToolSchema (OpenAI Compatible)

```python
class ToolSchema(TypedDict):
    name: str                                          # Unique tool name
    description: str                                   # Tool description
    parameters: JSONSchema                             # Parameter schema
```

#### JSONSchema

```python
class JSONSchema(TypedDict):
    type: Literal["object"]                           # Must be "object"
    properties: Dict[str, PropertySchema]             # Parameter definitions
    required: Optional[List[str]]                     # Required parameter names
    additionalProperties: Optional[bool]              # Allow extra properties
```

#### PropertySchema

```python
class PropertySchema(TypedDict):
    type: str                                         # "string", "integer", "number", "boolean", "array", "object"
    description: Optional[str]                        # Parameter description
    enum: Optional[List[Any]]                        # Allowed values
    minimum: Optional[Union[int, float]]             # Minimum value (numbers)
    maximum: Optional[Union[int, float]]             # Maximum value (numbers)
    minLength: Optional[int]                         # Minimum length (strings)
    maxLength: Optional[int]                         # Maximum length (strings)
    items: Optional["PropertySchema"]                # Array item schema
    default: Optional[Any]                           # Default value
```

#### ToolMetadata

```python
class ToolMetadata(TypedDict):
    conversation_id: Optional[str]                   # Current conversation ID
    timestamp: str                                   # ISO 8601 timestamp
    model_name: Optional[str]                        # AI model name
    tool_call_count: int                            # Number of tools called in response
```

### Function Signatures

#### Basic Function

```python
async def basic_tool(param1: str, param2: int) -> str:
    """
    Basic tool function.
    
    Args:
        param1: String parameter
        param2: Integer parameter
    
    Returns:
        String result
    
    Raises:
        ValueError: If parameters are invalid
    """
    return "Result"
```

#### Function with Metadata

```python
async def metadata_tool(param1: str, metadata: ToolMetadata) -> str:
    """
    Tool function with access to execution metadata.
    
    Args:
        param1: String parameter
        metadata: Execution context metadata
    
    Returns:
        String result
    """
    conversation_id = metadata["conversation_id"]
    timestamp = metadata["timestamp"]
    return f"Result for conversation {conversation_id} at {timestamp}"
```

### Simple Example: Calculator Tool

Here's a complete, working calculator tool that demonstrates the basic structure:

```python
# tools/calculator.py
from typing import Union

async def calculate(operation: str, a: float, b: float) -> str:
    """Perform basic math calculations."""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return "Error: Division by zero"
            result = a / b
        else:
            return f"Error: Unknown operation '{operation}'"
        
        return f"{a} {operation} {b} = {result}"
        
    except Exception as e:
        return f"Error: {str(e)}"

TOOLS = [
    {
        "function": calculate,
        "schema": {
            "name": "calculator",
            "description": "Perform basic math calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Math operation to perform",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number", 
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
    }
]
```

---

## Tool Configuration Features

### Auto Tools

Auto tools execute automatically before each AI response:

```python
TOOLS = [
    {
        "function": auto_background_task,
        "auto_tool": True,                            # Required: marks as auto-executing
        "schema": {
            "name": "background_task",
            "description": "Runs automatically on every response",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]
```

**Execution Flow:**
1. User sends message
2. Auto tools execute (in registration order)
3. AI generates response with tool results in context

### One-Time Tools

One-time tools can only be called once per AI response:

```python
TOOLS = [
    {
        "function": expensive_operation,
        "one_time": True,                             # Required: prevents multiple calls
        "schema": {
            "name": "expensive_op",
            "description": "Can only be called once per response",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to process"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

**Behavior:**
- First call: Executes normally
- Subsequent calls: Tool is not available in the same response

### Conditional Tools

Tools with dynamic availability based on runtime conditions:

```python
async def business_hours_check() -> bool:
    """Only available during business hours (9 AM - 5 PM)."""
    from datetime import datetime
    hour = datetime.now().hour
    return 9 <= hour <= 17

TOOLS = [
    {
        "function": business_operation,
        "condition": business_hours_check,            # Required: availability function
        "schema": {
            "name": "business_op",
            "description": "Only available during business hours",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]
```

**Condition Function Contract:**
- **Return Type:** `bool` or `Awaitable[bool]`
- **Execution:** Called every second to check availability
- **Failure Handling:** Exceptions hide the tool

### Status Reporter Functions

Add status reporting to display tool state in the dashboard:

```python
async def status_reporter(conversation_id: Optional[str] = None) -> str:
    """
    Status reporting function for dashboard display.
    
    Args:
        conversation_id: Optional conversation context
    
    Returns:
        Status message for display
    """
    return "Status: Active"

TOOLS = [
    {
        "report_status": status_reporter,             # Required: status function
        "schema": {
            "name": "system_status",
            "description": "System status display"
        }
    }
]
```

### Cleanup Functions

Cleanup functions run after response completion to handle resource cleanup:

```python
async def cleanup_handler() -> None:
    """
    Cleanup function called after response completion.
    
    Returns:
        None
    """
    # Perform cleanup operations
    print("Cleaning up resources...")
    # Close connections, clear temporary data, etc.

TOOLS = [
    {
        "function": resource_intensive_tool,
        "cleanup_function": cleanup_handler,          # Required: cleanup function
        "schema": {
            "name": "resource_tool",
            "description": "Tool that requires cleanup"
        }
    }
]
```

**Cleanup Function Contract:**
- **Return Type:** `None` or `Awaitable[None]`
- **Execution:** Called once after AI response is complete
- **Error Handling:** Exceptions are logged but don't affect the response

---

## Streaming Tools

### ResponseChunk API

```python
@dataclass
class ResponseChunk:
    type: Literal["assistant", "system", "context"]  # Content destination
    content: str                                     # Text content
```

**Constructor Functions:**
```python
def assistant_chunk(content: str) -> ResponseChunk:
    """Create assistant content chunk for streaming."""

def system_chunk(content: str) -> ResponseChunk:
    """Create system message chunk for streaming."""

def context_chunk(content: str) -> ResponseChunk:
    """Create tool role context message chunk for streaming."""
```

### Streaming Function Signature

```python
async def streaming_tool(param1: str) -> AsyncGenerator[ResponseChunk, None]:
    """
    Streaming tool function.
    
    Args:
        param1: String parameter
    
    Yields:
        ResponseChunk: Content chunks for streaming
    
    Returns:
        None (generator function)
    """
    yield assistant_chunk("Processing...")
    yield system_chunk("System notification")
    yield context_chunk("Web search results: The capital of France is Paris.")
    yield assistant_chunk("Complete!")
```

### Complete Streaming Example

```python
# tools/web_search.py
from utils.tool_utils import assistant_chunk, system_chunk, context_chunk
from typing import AsyncGenerator
import asyncio

async def web_search(query: str) -> AsyncGenerator[ResponseChunk, None]:
    """
    Perform web search with real-time progress and context updates.
    
    Args:
        query: Search query to process
    
    Yields:
        ResponseChunk: Progress updates and search results
    """
    yield assistant_chunk(f"Searching for: {query}...\n")

    # Simulate search steps
    yield system_chunk("🔍 Connecting to search API\n")
    await asyncio.sleep(0.5)
    
    yield assistant_chunk("Connected! Performing search...\n")
    await asyncio.sleep(1.0)  # Simulate API call
    
    # Provide context that the AI can reference in the same response
    search_results = f"Search results for '{query}': Found 3 relevant articles about web development best practices."
    yield context_chunk(search_results)
    
    yield assistant_chunk("Search complete! I now have the latest information to answer your question.\n")

TOOLS = [
    {
        "function": web_search,
        "schema": {
            "name": "web_search",
            "description": "Perform web search with real-time progress updates",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to process"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

### Streaming Event Flow

1. **Tool Call:** AI calls streaming tool
2. **Chunk Generation:** Tool yields ResponseChunk objects
3. **Content Routing:**
   - `assistant_chunk()` → Added to current AI response (visible to user and AI)
   - `system_chunk()` → Creates separate system message (visible to user and AI)
   - `context_chunk()` → Creates tool role message (hidden from user, visible to AI only)
4. **Real-time Display:** UI updates in real-time as chunks arrive
5. **Message Persistence:** Final content saved to conversation history

### Chunk Type Usage Patterns

**Use `assistant_chunk()` when:**
- Providing user-facing updates or results
- Showing progress or status messages
- Displaying tool output that should appear in the AI's response

**Use `system_chunk()` when:**
- Providing notifications visible to both user and AI
- Adding metadata or technical information that should be transparent
- Creating system messages that appear in the conversation

**Use `context_chunk()` when:**
- Providing private context data that only the AI should see
- Adding search results, API responses, or external data for AI reference
- Supplying background information that enhances the AI's knowledge without cluttering the user interface

---

## UI Tools

UI tools create interactive components that appear in the Ghostpad interface. They can be simple widgets or complex modal interfaces with forms and data displays.

### Simple Widgets

Display data from KV store as formatted text:

```python
TOOLS = [
    {
        "schema": {"name": "balance_widget", "description": "Balance display"},
        "ui_feature": {
            "id": "user_balance",                   # Unique widget ID
            "label": "Balance",                     # Display label
            "kv_key": "user_balance",              # KV store key for data
            "type": "widget",                       # UI type
            "widget_config": {
                "type": "text",                     # Widget type
                "format_options": {
                    "max_length": 20,
                    "truncate": True,
                    "text": {
                        "prefix": "$",              # Show as "$1000"
                        "color": "green"
                    }
                }
            }
        }
    }
]
```

### Complete Modal UI Example: Settings Manager

Here's a comprehensive example that shows how to create a modal with form components, data sources, and event handlers:

```python
# tools/settings_manager.py
from services.kv_store_service import kv_store
from typing import Dict, Any, Optional

async def save_settings_handler(
    params: Dict[str, Any], 
    metadata: Optional[ToolMetadata] = None
) -> UIHandlerResponse:
    """
    Handle settings form submission.
    
    Args:
        params: {"username": "john", "email": "john@example.com", "theme": "dark"}
        metadata: Execution context
    
    Returns:
        UI response with success/error state
    """
    username = params.get("username", "").strip()
    email = params.get("email", "").strip()
    theme = params.get("theme", "light")
    
    # Validation
    if not username:
        return {
            "success": False,
            "error": "Username is required"
        }
    
    if "@" not in email:
        return {
            "success": False, 
            "error": "Invalid email address"
        }
    
    try:
        # Save settings
        await kv_store.set("user_username", username)
        await kv_store.set("user_email", email)
        await kv_store.set("user_theme", theme)
        
        return {
            "success": True,
            "message": "Settings saved successfully",
            "clear_inputs": [],  # Don't clear inputs to preserve values
            "refresh_components": ["settings_table"],
            "close_modal": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save settings: {str(e)}"
        }

TOOLS = [
    {
        "schema": {"name": "settings_ui", "description": "User settings interface"},
        "ui_feature": {
            "id": "settings_modal",
            "type": "ui_v1",
            "label": "Settings",
            "icon": "Settings",
            "layout": {
                "type": "modal",
                "size": "md",
                "title": "User Settings",
                "components": [
                    # Display current settings in a table
                    {
                        "id": "settings_table",
                        "type": "table_display",
                        "data_source": {
                            "type": "persona_properties",
                            "key": "settings",
                            "include_user": True
                        },
                        "props": {
                            "height": "150px",
                            "show_refresh": True,
                            "columns": [
                                {"key": "name", "label": "Setting", "format": "text"},
                                {"key": "value", "label": "Value", "format": "text"}
                            ]
                        }
                    },
                    
                    # Form section header
                    {
                        "id": "form_header",
                        "type": "html_renderer",
                        "data_source": {
                            "type": "value",
                            "value": "<h3>Update Settings</h3>"
                        }
                    },
                    
                    # Username input (loads current value from KV store)
                    {
                        "id": "username_input",
                        "type": "text_input",
                        "data_source": {"type": "kv_store", "key": "user_username"},
                        "props": {
                            "placeholder": "Enter username",
                            "max_length": 50
                        }
                    },
                    
                    # Email input
                    {
                        "id": "email_input", 
                        "type": "text_input",
                        "data_source": {"type": "kv_store", "key": "user_email"},
                        "props": {
                            "placeholder": "Enter email address",
                            "width": "100%"
                        }
                    },
                    
                    # Theme selector using persona selector as dropdown
                    {
                        "id": "theme_selector",
                        "type": "persona_selector",
                        "props": {
                            "placeholder": "Select theme",
                            "include_user": False
                        }
                    },
                    
                    # Action buttons
                    {
                        "id": "save_button",
                        "type": "button",
                        "props": {
                            "label": "Save Settings", 
                            "variant": "primary",
                            "size": "md"
                        },
                        "actions": [
                            {
                                "type": "tool_submit",
                                "trigger": "click", 
                                "target": "save_settings",
                                "params": {
                                    "username": "username_input",
                                    "email": "email_input",
                                    "theme": "theme_selector"
                                }
                            }
                        ]
                    }
                ]
            }
        },
        "ui_handlers": {
            "save_settings": save_settings_handler
        }
    }
]
```

### UI Component Reference

#### Common Components

**Text Input:**
```python
{
    "id": "my_input",
    "type": "text_input",
    "props": {
        "placeholder": "Enter text",
        "max_length": 100,
        "width": "200px",
        "disabled": False
    },
    "data_source": {"type": "kv_store", "key": "my_value"}
}
```

**Number Input:**
```python
{
    "id": "amount_input",
    "type": "number_input",
    "props": {
        "placeholder": "Enter amount",
        "min": 0,
        "max": 1000,
        "step": 1
    }
}
```

**Button:**
```python
{
    "id": "submit_btn",
    "type": "button",
    "props": {
        "label": "Submit",
        "variant": "primary",  # primary, secondary, danger
        "size": "md"          # sm, md, lg
    },
    "actions": [{
        "type": "tool_submit",
        "trigger": "click",
        "target": "my_handler",
        "params": {"field": "input_id"}
    }]
}
```

**Table Display:**
```python
{
    "id": "data_table",
    "type": "table_display",
    "data_source": {
        "type": "persona_properties",
        "key": "balance",
        "include_user": True
    },
    "props": {
        "height": "300px",
        "columns": [
            {"key": "name", "label": "Name", "format": "text"},
            {"key": "balance", "label": "Balance", "format": "currency"}
        ]
    }
}
```

### Data Sources

**KV Store:** `{"type": "kv_store", "key": "setting_name"}`
**Static Value:** `{"type": "value", "value": "Static content"}`
**Persona Properties:** `{"type": "persona_properties", "key": "property_name", "include_user": true}`

### Handler Response Format

```python
# Success response
{
    "success": True,
    "message": "Operation completed successfully",
    "clear_inputs": ["input1", "input2"],        # Clear these components
    "refresh_components": ["table1"],            # Refresh these components
    "close_modal": True                          # Close the modal
}

# Error response
{
    "success": False,
    "error": "Validation failed: Email is required"
}
```

---

## Service Integration

### Available Services

```python
# KV Store - Persistent key-value storage
from services.kv_store_service import kv_store

value = await kv_store.get("key", default_value)
await kv_store.set("key", value)
await kv_store.delete("key")

# Persona Service - Access persona information
from services.persona_service import persona_service

persona_names = await persona_service.get_persona_names_for_conversation(conversation_id)

# Utility Functions - Helper functions
from utils.tool_utils import create_system_message_in_conversation

message_id = await create_system_message_in_conversation("content", conversation_id)
```

---

## Error Handling

### Tool Function Errors

```python
async def robust_tool(param: str) -> str:
    """Tool with comprehensive error handling."""
    try:
        if not param.strip():
            raise ValueError("Parameter cannot be empty")
            
        result = await external_api_call(param)
        return f"Success: {result}"
        
    except ValueError as e:
        return f"Validation error: {e}"
    except ConnectionError as e:
        return f"Connection failed: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in robust_tool: {e}")
        return f"Operation failed: Please try again"
```

### UI Handler Errors

```python
async def error_handling_ui_handler(params: Dict[str, Any]) -> UIHandlerResponse:
    """UI handler with proper error handling."""
    try:
        # Process request
        result = await process_request(params)
        
        return {
            "success": True,
            "message": f"Operation completed: {result}"
        }
        
    except ValidationError as e:
        return {
            "success": False,
            "error": f"Invalid input: {e}"
        }
    except PermissionError as e:
        return {
            "success": False,
            "error": f"Access denied: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error in UI handler: {e}")
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }
```

### Condition Function Errors

```python
async def safe_condition() -> bool:
    """Condition function with error handling."""
    try:
        # Check external condition
        return await check_external_status()
    except Exception as e:
        logger.error(f"Condition check failed: {e}")
        return False  # Default to unavailable on error
```

---

## Complete Examples

The document includes complete, working examples throughout each section:

- **Basic Tools:** Calculator tool in [Basic Tool Creation](#basic-tool-creation)
- **Streaming Tools:** File processor in [Streaming Tools](#streaming-tools)  
- **UI Tools:** Settings manager in [UI Tools](#ui-tools)
- **Configuration Features:** Business hours tool with cleanup in [Tool Configuration Features](#tool-configuration-features)

Each example shows the complete implementation including function definitions, tool schemas, and TOOLS registration arrays that you can copy and use directly.

---

This comprehensive API reference provides everything developers need to build sophisticated tools for the Ghostpad system. Each section includes practical examples that demonstrate real-world usage patterns.