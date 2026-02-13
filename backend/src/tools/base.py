"""工具基类。

定义所有工具的抽象基类。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """工具抽象基类。

    所有工具必须继承此类并实现 get_parameters 和 execute 方法。
    """

    def __init__(self, name: str, description: str):
        """初始化工具。

        Args:
            name: 工具名称
            description: 工具描述，供 LLM 理解工具用途
        """
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """获取工具名称。"""
        return self._name

    @property
    def description(self) -> str:
        """获取工具描述。"""
        return self._description

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。

        Returns:
            JSON Schema 格式的参数定义
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具逻辑。

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果字典

        Raises:
            ValueError: 参数无效或执行失败
        """
        pass

    async def ainvoke(self, **kwargs: Any) -> Dict[str, Any]:
        """异步执行工具逻辑。

        默认实现调用同步的 execute 方法。
        子类可以重写此方法以支持真正的异步执行。

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果字典

        Raises:
            ValueError: 参数无效或执行失败
        """
        # 默认实现：在线程池中执行同步的 execute 方法
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))

    def get_schema(self) -> Dict[str, Any]:
        """获取完整的工具 schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters(),
            }
        }

    def __repr__(self) -> str:
        return f"BaseTool(name={self.name})"
