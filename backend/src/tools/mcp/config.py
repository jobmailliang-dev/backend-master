"""MCP configuration loader."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from src.config.dotenv_loader import expand_env_in_dict


DEFAULT_CONFIG_FILES = (
    "mcp_servers.json",
    ".mcp.json",
    "mcp.json",
)


def _load_from_env() -> dict[str, Any] | None:
    raw = os.environ.get("MCP_SERVERS")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        # 替换环境变量
        return expand_env_in_dict(data)
    except json.JSONDecodeError:
        return None


def _load_from_files(project_root: str) -> dict[str, Any] | None:
    root = Path(project_root)
    for name in DEFAULT_CONFIG_FILES:
        path = root / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # 替换环境变量
            return expand_env_in_dict(data)
        except Exception:
            continue
    return None


def load_mcp_servers(project_root: str) -> dict[str, Any]:
    data = _load_from_env() or _load_from_files(project_root)
    if not data:
        return {}
    if "mcpServers" in data and isinstance(data["mcpServers"], dict):
        return data["mcpServers"]
    if isinstance(data, dict):
        return data
    return {}


def connect_mode() -> str:
    return os.environ.get("MCP_CONNECT_MODE", "startup").lower()
