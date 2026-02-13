"""适配器基类。

定义 LLM API 适配器的抽象接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional


@dataclass
class LLMResponse:
    """LLM 响应统一类型。"""
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_content: str = ""  # Qwen thinking 模式下的思考过程
    llm_provider: str = "openai"  # 模型提供商: openai, qwen

    def get_thinking_content(self) -> str:
        """获取思考内容。

        - Qwen: 返回 reasoning_content
        - OpenAI: 如果有 tool_calls 返回 content，否则返回空字符串
        """
        if self.llm_provider == "qwen":
            return self.reasoning_content
        else:
            # OpenAI: 有工具调用时，content 作为 thinking 内容
            return self.content if self.tool_calls else ""


class LLMAdapter(ABC):
    """LLM API 适配器基类。"""

    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> LLMResponse:
        """发起 API 请求。

        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            LLMResponse: AI 回复内容
        """
        pass

    @abstractmethod
    def complete_stream(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        """流式发起 API 请求。

        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数（temperature, max_tokens 等）

        Yields:
            包含 content、tool_calls、reasoning_content 的字典
        """
        pass

    @abstractmethod
    def complete_auto(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> LLMResponse:
        """根据配置自动选择流式或非流式调用。

        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            LLMResponse: 包含 content、tool_calls、reasoning_content 的响应
        """
        pass
