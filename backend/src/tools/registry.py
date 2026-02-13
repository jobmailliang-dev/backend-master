"""工具注册表。

管理工具的注册和执行。
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from src.tools.base import BaseTool


class ToolRegistry:
    """工具注册表。

    提供工具的注册、查找和执行功能。
    """

    # 终端颜色代码
    _GRAY = "\033[90m" if sys.stdout.isatty() else ""
    _RESET = "\033[0m" if sys.stdout.isatty() else ""

    def __init__(self):
        """初始化工具注册表。"""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具。

        Args:
            tool: 工具实例

        Raises:
            ValueError: 如果工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具。

        Args:
            name: 工具名称

        Returns:
            工具实例，不存在返回 None
        """
        return self._tools.get(name)

    def list_all(self) -> List[str]:
        """列出所有已注册的工具名称。

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def execute(self, name: str, **kwargs: Any) -> str:
        """执行工具。

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            JSON 格式的执行结果

        Raises:
            ValueError: 工具不存在或执行失败
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        try:
            if not isinstance(kwargs, dict):
                raise ValueError(f"Arguments must be dict, got {type(kwargs)}")

            result = tool.execute(**kwargs)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"Tool execution failed: {str(e)}")

    async def aexecute(self, name: str, **kwargs: Any) -> str:
        """异步执行工具。

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            JSON 格式的执行结果

        Raises:
            ValueError: 工具不存在或执行失败
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        try:
            if not isinstance(kwargs, dict):
                raise ValueError(f"Arguments must be dict, got {type(kwargs)}")

            # 调用工具的异步方法
            result = await tool.ainvoke(**kwargs)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"Tool execution failed: {str(e)}")

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 schema。"""
        return [tool.get_schema() for tool in self._tools.values()]

    def print_tool_call(self, iteration: int, name: str, args: Dict[str, Any]) -> None:
        """打印工具调用信息。"""
        args_str = str(args)
        max_len = 1000
        if len(args_str) > max_len:
            args_str = args_str[:max_len] + "..."

        print(f"\n{self._GRAY}[Tool Call #{iteration}] {self._RESET}"
              f"{self._GRAY}{name} {self._RESET}with args: {self._GRAY}{args_str}{self._RESET}")

    def print_tool_result(self, name: str, result: str, max_len: int = 500) -> None:
        """打印工具执行结果。"""
        result_str = str(result)
        if len(result_str) > max_len:
            result_str = result_str[:max_len] + "..."

        print(f"{self._GRAY}[Tool Result] {self._RESET}"
              f"{self._GRAY}{name}: {result_str}{self._RESET}\n")

    def print_tool_error(self, error_msg: str) -> None:
        """打印工具错误信息。"""
        print(f"{self._GRAY}[Tool Error] {self._RESET}"
              f"{self._GRAY}{error_msg}{self._RESET}\n")


# 全局注册表实例
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """获取全局工具注册表。"""
    return _registry


def register_tool(tool: BaseTool) -> None:
    """向全局注册表注册工具。"""
    _registry.register(tool)
