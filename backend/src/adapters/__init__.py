"""API 适配器模块。

提供 LLM API 的适配器实现。
"""

from typing import TYPE_CHECKING

from src.adapters.base import LLMAdapter, LLMResponse
from src.adapters.openai import OpenAIClientAdapter
from src.adapters.qwen import QwenClientAdapter

from src.config.models import LLMConfig


def get_adapter(llm_type: str, config: LLMConfig) -> LLMAdapter:
    """根据 LLM 类型实例化适配器。

    Args:
        llm_type: LLM 提供商类型，支持 "openai" 和 "qwen"
        config: LLM 配置对象

    Returns:
        LLMAdapter: 适配器实例

    Raises:
        ValueError: 当不支持的 llm_type 时抛出
    """
    llm_type = llm_type.lower()

    if llm_type == "qwen":
        return QwenClientAdapter(config)
    elif llm_type == "openai":
        return OpenAIClientAdapter(config)
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}. Supported types: openai, qwen")


__all__ = ['OpenAIClientAdapter', 'QwenClientAdapter', 'LLMResponse', 'get_adapter']
