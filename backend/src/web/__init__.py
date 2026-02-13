"""Web 模块初始化。"""

from .sse import SSEStreamer
from .cors import setup_cors

__all__ = ["SSEStreamer", "setup_cors"]
