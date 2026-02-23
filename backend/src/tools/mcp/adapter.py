"""Adapters for MCP tools to ToolRegistry."""

from __future__ import annotations

import time
from typing import Any

import logging
import re

from src.tools.base import BaseTool, ToolParameter, ErrorCode
from src.tools.mcp.protocol import to_protocol_result, to_protocol_error, to_protocol_invalid_param


class MCPToolAdapter(BaseTool):
    """Wrap an MCP tool and expose it as a BaseTool."""

    def __init__(
        self,
        mcp_client,
        public_name: str,
        remote_name: str,
        tool_description: str | None = None,
        schema: dict | None = None,
    ):
        super().__init__(name=public_name, description=tool_description or "MCP tool")
        self._mcp_client = mcp_client
        self._remote_name = remote_name
        self._schema = schema or {}
        self._parameters: list[ToolParameter] = []

        # 初始化参数列表
        self._init_parameters()

    def _init_parameters(self) -> None:
        """初始化参数列表。"""
        schema = self._schema if isinstance(self._schema, dict) else {}
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return
        required = set(schema.get("required") or [])
        for name, spec in properties.items():
            if isinstance(spec, dict):
                type_name = spec.get("type") or "any"
                description = (spec.get("description") or "").strip()
                default = spec.get("default")
            else:
                type_name = "any"
                description = ""
                default = None
            param = ToolParameter(
                name=name,
                type=type_name,
                description=description,
                required=name in required,
                default=default,
            )
            self._parameters.append(param)

    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义（JSON Schema 格式）。"""
        schema = self._schema if isinstance(self._schema, dict) else {}
        return schema

    def invoke(self, **kwargs: Any) -> dict[str, Any]:
        """执行工具逻辑（同步）。"""
        start_time = time.monotonic()
        try:
            invalid = self._validate_params(kwargs)
            if invalid:
                error_result = to_protocol_invalid_param(
                    invalid, kwargs, self._remote_name, start_time
                )
                return {"error": error_result}
        except Exception as exc:
            message = str(exc) or repr(exc)
            error_result = to_protocol_error(
                message, kwargs, self._remote_name, start_time, ErrorCode.MCP_PARSE_ERROR
            )
            return {"error": error_result}

        try:
            result = self._mcp_client.call_tool_sync(self._remote_name, kwargs)
        except TimeoutError as exc:
            message = str(exc) or "MCP tool call timeout"
            error_result = to_protocol_error(
                message, kwargs, self._remote_name, start_time, ErrorCode.MCP_TIMEOUT
            )
            return {"error": error_result}
        except ConnectionError as exc:
            message = str(exc) or "MCP server connection failed"
            error_result = to_protocol_error(
                message, kwargs, self._remote_name, start_time, ErrorCode.MCP_NETWORK_ERROR
            )
            return {"error": error_result}
        except Exception as exc:
            message = str(exc) or repr(exc)
            error_result = to_protocol_error(
                message, kwargs, self._remote_name, start_time, ErrorCode.MCP_EXECUTION_ERROR
            )
            return {"error": error_result}

        try:
            protocol_result = to_protocol_result(result, kwargs, self._remote_name, start_time)
            return {"result": protocol_result, "text": protocol_result}
        except Exception as exc:
            message = str(exc) or repr(exc)
            error_result = to_protocol_error(
                message, kwargs, self._remote_name, start_time, ErrorCode.MCP_PARSE_ERROR
            )
            return {"error": error_result}

    def _validate_params(self, parameters: dict[str, Any]) -> str:
        schema = self._schema if isinstance(self._schema, dict) else {}
        properties = schema.get("properties")
        required = schema.get("required") or []
        if not isinstance(properties, dict):
            return ""
        missing = [name for name in required if name not in parameters]
        additional = schema.get("additionalProperties", True)
        allow_unknown = additional is not False
        unknown = []
        if not allow_unknown:
            unknown = [name for name in parameters.keys() if name not in properties]
        parts = []
        if missing:
            parts.append(f"missing required params: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown params: {', '.join(unknown)}")
        return "; ".join(parts)


def register_mcp_tools(tool_registry, mcp_client, namespace: str | None = None) -> list[dict[str, object | None]]:
    """Discover tools from MCP server and register them to ToolRegistry."""
    logger = logging.getLogger(__name__)
    safe_name_pattern = re.compile(r"[^a-zA-Z0-9_-]")

    def sanitize_tool_name(name: str) -> str:
        sanitized = safe_name_pattern.sub("_", name)
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        return sanitized or "tool"

    def ensure_unique(base_name: str) -> str:
        candidate = base_name
        counter = 2
        while tool_registry.get(candidate):
            candidate = f"{base_name}_{counter}"
            counter += 1
        return candidate

    tools = mcp_client.list_tools_sync()
    registered: list[dict[str, object | None]] = []
    for tool in tools.tools:
        remote_name = getattr(tool, "name", None) or getattr(tool, "tool_name", None)
        description = getattr(tool, "description", None)
        schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
        if hasattr(schema, "model_dump"):
            schema = schema.model_dump()
        if not remote_name:
            continue
        raw_public_name = f"{namespace}:{remote_name}" if namespace else remote_name
        public_name = sanitize_tool_name(raw_public_name)
        public_name = ensure_unique(public_name)
        if public_name != raw_public_name:
            logger.info("Sanitized MCP tool name '%s' -> '%s'", raw_public_name, public_name)
        adapter = MCPToolAdapter(mcp_client, public_name, remote_name, description, schema)
        tool_registry.register(adapter)
        registered.append({"name": public_name, "description": description, "schema": schema})
    return registered
