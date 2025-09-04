"""
Tool management service for Ghostpad.

This service handles:
- Tool discovery and loading from the tools/ directory
- Tool registry management and persistence
- Tool execution and status reporting
- Auto-tool execution
- Tool condition checking and UI feature extraction
"""

import json
import os
import sys
import asyncio
import inspect
import importlib.util
from typing import Dict, Any, List, Tuple
from datetime import datetime
from services.state_service import state_service
from services.kv_store_service import kv_store
from services.websocket_service import websocket_service
from services.log_service import logger

class ToolService:
    """Service for managing tools in Ghostpad."""

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}

    def get_enabled_tools(self) -> List[Dict[str, Any]]:
        """Return enabled tool definitions from the in-memory registry."""
        return [t for t in self.registry.values() if t.get("enabled")]

    def build_tool_prompt(
        self, tools_used: List[str], tools: List[Dict[str, Any]]
    ) -> str:
        """Construct a tool availability prompt (excluding auto tools and respecting one_time)."""
        lines = ["You have access to the following tool(s):"]
        for t in tools:
            if not callable(t.get("function")):
                continue
            if t.get("auto_tool"):
                continue
            schema = t.get("schema", {})
            name = schema.get("name")
            print("oofie", name, t.get("function"))
            if not name:
                continue
            if t.get("one_time") and name in tools_used:
                continue
            desc = schema.get("description", "")
            lines.append(f"- {name}(...): {desc}")
        lines.append(
            "Use tool calls only when there is a good reason. If you have any tools which help you think or reason, use them often. When you have enough information to respond, stop making tool calls and respond to the user."
        )
        return "\n".join(lines)

    async def run_auto_tools_and_status(
        self, tools: List[Dict[str, Any]], conversation_id: str = None
    ) -> str:
        """Run auto tools (best-effort) and collect report_status results into a dashboard section."""
        status_lines: List[str] = []
        for t in tools:
            has_fn = callable(t.get("function"))
            report = t.get("report_status")
            has_report_status = callable(report)
            if not has_fn and not has_report_status:
                continue
            if has_fn and t.get("auto_tool"):
                tool_fn = t.get("function")
                try:
                    if inspect.iscoroutinefunction(tool_fn):
                        await tool_fn()
                    else:
                        result = tool_fn()
                        if inspect.iscoroutine(result):
                            await result
                except Exception as e:
                    print(f"[Ghostpad] Auto Tool Error: {e}")
            if has_report_status:
                try:
                    # Check if the report function accepts conversation_id
                    sig = inspect.signature(report)
                    if "conversation_id" in sig.parameters:
                        if inspect.iscoroutinefunction(report):
                            val = await report(conversation_id=conversation_id)
                        else:
                            val = report(conversation_id=conversation_id)
                            if inspect.iscoroutine(val):
                                val = await val
                    else:
                        if inspect.iscoroutinefunction(report):
                            val = await report()
                        else:
                            val = report()
                            if inspect.iscoroutine(val):
                                val = await val
                except Exception as e:
                    val = f"(Status error: {e})"
                if val:
                    status_lines.append(str(val))
        return (
            "\n---\n"
            + (
                "<STATUS_DASHBOARD>\n"
                + "\n".join(status_lines)
                + "\n</STATUS_DASHBOARD>"
            )
            if status_lines
            else "(No status reported)"
        ) + "\n---"

    async def load_tools(self, tools_dir: str = None):
        """Discover tools in the tools/ directory, validate and cache them.
        Persists enabled tool list in the simple key-value store under key 'enabled_tools'.
        """
        if tools_dir is None:
            tools_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "tools"
            )

        registry: Dict[str, Dict[str, Any]] = {}

        # Load enabled set from persistence
        enabled_ids: List[str] = await kv_store.get("enabled_tools", []) or []
        enabled_set = set(enabled_ids)

        if not os.path.isdir(tools_dir):
            self.registry = registry
            return

        for root, dirs, files in os.walk(tools_dir):
            for entry in files:
                if not entry.endswith(".py"):
                    continue
                if entry.startswith("_"):
                    continue

                # Create module name based on relative path from tools_dir
                rel_path = os.path.relpath(root, tools_dir)
                if rel_path == ".":
                    module_name = entry[:-3]
                else:
                    # Replace path separators with dots for nested modules
                    module_name = f"{rel_path.replace(os.sep, '.')}.{entry[:-3]}"

                module_path = os.path.join(root, entry)

                try:
                    spec = importlib.util.spec_from_file_location(
                        f"tools.{module_name}", module_path
                    )
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    # type: ignore[attr-defined]
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"[Ghostpad] Failed to load tool module {module_name}: {e}")
                    # Skip modules that fail to import
                    continue

                tools_list = getattr(module, "TOOLS", None)
                if not isinstance(tools_list, list):
                    continue

                for item in tools_list:
                    try:
                        if not isinstance(item, dict):
                            continue
                        fn = item.get("function")
                        schema = item.get("schema")
                        auto_tool = bool(item.get("auto_tool", False))
                        one_time = bool(item.get("one_time", False))
                        report_status = item.get("report_status")
                        ui_feature = item.get("ui_feature")
                        ui_handlers = item.get("ui_handlers")
                        condition = item.get("condition")

                        if not isinstance(schema, dict):
                            continue
                        name = schema.get("name")
                        description = schema.get("description", "")
                        parameters = schema.get(
                            "parameters",
                            {"type": "object", "properties": {}, "required": []},
                        )
                        if not isinstance(name, str) or not name:
                            continue
                        if callable(fn) and not isinstance(parameters, dict):
                            continue

                        tool_id = f"{module_name}.{name}"

                        # Check if tool supports streaming and metadata by inspecting its signature
                        supports_metadata = False
                        try:
                            sig = inspect.signature(fn)
                            supports_metadata = "metadata" in sig.parameters
                        except Exception:
                            # If signature inspection fails, assume no streaming or metadata support
                            supports_metadata = False

                        registry[tool_id] = {
                            "id": tool_id,
                            "name": name,
                            "description": description,
                            "module": module_name,
                            "function": fn,
                            "report_status": (
                                report_status if callable(report_status) else None
                            ),
                            "cleanup_function": (
                                item.get("cleanup_function")
                                if callable(item.get("cleanup_function"))
                                else None
                            ),
                            "auto_tool": auto_tool,
                            "one_time": one_time,
                            "condition": condition if callable(condition) else None,
                            "schema": {
                                "name": name,
                                "description": description,
                                "parameters": parameters,
                            },
                            "enabled": tool_id in enabled_set,
                            "ui_feature": (
                                ui_feature if isinstance(ui_feature, dict) else None
                            ),
                            "ui_handlers": (
                                ui_handlers if isinstance(ui_handlers, dict) else None
                            ),
                            "supports_metadata": supports_metadata,
                        }
                    except Exception:
                        continue

        self.registry = registry
        try:
            if not registry:
                print("[Ghostpad] Tools: none found")
            else:
                print(f"[Ghostpad] Tools detected ({len(registry)}):")
                for tool in sorted(registry.values(), key=lambda t: t["id"]):
                    status = "enabled" if tool.get("enabled") else "disabled"
                    flags = []
                    if tool.get("auto_tool"):
                        flags.append("auto")
                    if tool.get("one_time"):
                        flags.append("one-time")
                    if tool.get("ui_feature"):
                        flags.append("ui")
                    if tool.get("supports_metadata"):
                        flags.append("metadata")
                    if tool.get("condition"):
                        flags.append("conditional")
                    flags_str = f" ({', '.join(flags)})" if flags else ""
                    print(f"  - {tool['id']} [{status}]{flags_str}")
        except Exception:
            pass

    def get_tools_registry(self) -> Dict[str, Dict[str, Any]]:
        """Get the tools registry."""
        return self.registry

    def get_tool_by_id(self, tool_id: str) -> Dict[str, Any] | None:
        """Get a tool by its ID."""
        return self.registry.get(tool_id)

    async def toggle_tool(self, tool_id: str, enabled: bool) -> bool:
        """Enable or disable a tool by id, and persist the selection."""
        if tool_id not in self.registry:
            return False

        # Update in-memory
        self.registry[tool_id]["enabled"] = enabled

        # Persist enabled set
        enabled_ids: List[str] = await kv_store.get("enabled_tools", []) or []
        enabled_set = set(enabled_ids)
        if enabled:
            enabled_set.add(tool_id)
        else:
            enabled_set.discard(tool_id)
        await kv_store.set("enabled_tools", sorted(enabled_set))

        return True

    async def toggle_file_tools(self, module_name: str, enabled: bool) -> bool:
        """Enable or disable all tools in a file."""
        # Find all tools in the specified module
        tools_in_module = [
            tool_id
            for tool_id, tool in self.registry.items()
            if tool.get("module", "") == module_name
        ]

        if not tools_in_module:
            return False

        # Update all tools in the module
        for tool_id in tools_in_module:
            self.registry[tool_id]["enabled"] = enabled

        # Persist enabled set
        enabled_ids: List[str] = await kv_store.get("enabled_tools", []) or []
        enabled_set = set(enabled_ids)

        for tool_id in tools_in_module:
            if enabled:
                enabled_set.add(tool_id)
            else:
                enabled_set.discard(tool_id)

        await kv_store.set("enabled_tools", sorted(enabled_set))

        return True

    async def get_tool_features(self) -> List[Dict[str, Any]]:
        """List UI features derived from enabled tools."""
        features: List[Dict[str, Any]] = []
        for tool in self.registry.values():
            if not tool.get("enabled"):
                continue

            # Check condition function if present
            condition_fn = tool.get("condition")
            if callable(condition_fn):
                try:
                    condition_result = await condition_fn()
                    if not condition_result:
                        continue  # Skip this tool's UI feature if condition fails
                except Exception as e:
                    print(f"Error checking condition for tool {tool.get('id')}: {e}")
                    continue  # Skip if condition check fails

            feat = tool.get("ui_feature")
            if isinstance(feat, dict):
                # attach source id for traceability
                f = dict(feat)
                f["source_tool_id"] = tool.get("id")
                features.append(f)
        return features

    def find_ui_handler(self, handler_name: str) -> Tuple[Any, Dict[str, Any]]:
        """Find a UI handler function from enabled tools.
        
        Returns:
            Tuple of (handler_function, tool_dict) or raises ValueError if not found
        """
        for tool in self.registry.values():
            if not tool.get("enabled"):
                continue

            ui_handlers = tool.get("ui_handlers", {})
            if ui_handlers and handler_name in ui_handlers:
                return ui_handlers[handler_name], tool
        
        raise ValueError(f"UI handler '{handler_name}' not found in any enabled tool")

    async def execute_ui_handler(self, handler_name: str, params: Dict[str, Any], conversation_id: str = None) -> Any:
        """Execute a UI handler function with proper metadata and signature handling.
        
        Args:
            handler_name: Name of the handler to execute
            params: Parameters to pass to the handler
            conversation_id: Optional conversation ID for metadata
            
        Returns:
            The result of the handler execution
        """
        handler_function, _ = self.find_ui_handler(handler_name)
        
        # Create metadata object consistent with chat_service.py
        metadata = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Execute the handler function with metadata support
        sig = inspect.signature(handler_function)
        supports_metadata = "metadata" in sig.parameters

        if inspect.iscoroutinefunction(handler_function):
            if supports_metadata:
                result = await handler_function(params, metadata)
            else:
                result = await handler_function(params)
        else:
            if supports_metadata:
                result = handler_function(params, metadata)
            else:
                result = handler_function(params)
            if inspect.iscoroutine(result):
                result = await result

        return result

    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of tools formatted for API response."""
        tools = []
        for tool in self.registry.values():
            tools.append({
                "id": tool["id"],
                "name": tool["name"],
                "description": tool.get("description", ""),
                "module": tool.get("module", ""),
                "enabled": bool(tool.get("enabled", False)),
                "auto_tool": bool(tool.get("auto_tool", False)),
                "one_time": bool(tool.get("one_time", False)),
                "condition": (
                    bool(tool.get("condition")) if tool.get("condition") else None
                ),
                "parameters": tool.get("parameters", {}),
                "ui_feature": tool.get("ui_feature"),
            })
        return tools

    def get_tools_by_file(self) -> List[Dict[str, Any]]:
        """Get tools grouped by file with file-level metadata."""
        files = {}

        for tool in self.registry.values():
            module_name = tool.get("module", "unknown")
            if module_name not in files:
                files[module_name] = {
                    "name": module_name,
                    "tools": [],
                    "enabled_count": 0,
                    "total_count": 0,
                    "all_enabled": True,
                    "any_enabled": False,
                }

            tool_info = {
                "id": tool["id"],
                "name": tool["name"],
                "description": tool.get("description", ""),
                "module": tool.get("module", ""),
                "enabled": bool(tool.get("enabled", False)),
                "auto_tool": bool(tool.get("auto_tool", False)),
                "one_time": bool(tool.get("one_time", False)),
                "condition": (
                    bool(tool.get("condition")) if tool.get("condition") else None
                ),
                "parameters": tool.get("parameters", {}),
                "ui_feature": tool.get("ui_feature"),
            }

            files[module_name]["tools"].append(tool_info)
            files[module_name]["total_count"] += 1

            if tool_info["enabled"]:
                files[module_name]["enabled_count"] += 1
                files[module_name]["any_enabled"] = True
            else:
                files[module_name]["all_enabled"] = False

        return list(files.values())

    async def cleanup_tools(self):
        """Run cleanup functions from enabled tools."""
        enabled_tools = self.get_enabled_tools()
        for t in enabled_tools:
            cleanup_fn = t.get("cleanup_function")
            if callable(cleanup_fn):
                try:
                    if inspect.iscoroutinefunction(cleanup_fn):
                        await cleanup_fn()
                    else:
                        res = cleanup_fn()
                        if inspect.iscoroutine(res):
                            await res
                except Exception as ce:
                    print(
                        f"[Ghostpad] Cleanup function error for tool {t.get('schema', {}).get('name')}: {ce}"
                    )

    async def check_tool_conditions(self):
        """Periodically check all tool condition functions and emit events when they change."""

        while True:
            try:
                await asyncio.sleep(1)  # Check every second

                registry = self.get_tools_registry()
                changes_detected = False

                for tool_id, tool in registry.items():
                    if not tool.get("enabled"):
                        continue

                    condition_fn = tool.get("condition")
                    if not callable(condition_fn):
                        continue

                    try:
                        current_result = await condition_fn()

                        previous_result = state_service.condition_results_cache.get(tool_id)

                        # Check if condition result changed
                        if previous_result != current_result:
                            state_service.condition_results_cache[tool_id] = current_result
                            changes_detected = True
                            logger.info(
                                f"Condition changed for tool {tool_id}: {previous_result} -> {current_result}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error checking condition for tool {tool_id}: {e}"
                        )

                if changes_detected:
                    event_data = {"type": "features_changed"}

                    try:
                        await websocket_service.broadcast_to_all(event_data)
                    except Exception as e:
                        logger.error(
                            f"Error broadcasting features_changed to WebSocket clients: {e}"
                        )

            except Exception as e:
                logger.error(f"Error in condition checking task: {e}")
                await asyncio.sleep(5)  # Back off on error


# Global tool service instance
tool_service = ToolService()
