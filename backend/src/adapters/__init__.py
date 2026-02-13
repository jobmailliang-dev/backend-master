"""API 适配器模块。

提供 LLM API 的适配器实现。
"""

from src.adapters.base import LLMResponse
from src.adapters.openai import OpenAIClientAdapter
from src.adapters.qwen import QwenClientAdapter

__all__ = ['OpenAIClientAdapter', 'QwenClientAdapter', 'LLMResponse']
