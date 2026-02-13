"""API 路由模块。"""

from .chat import router as chat_router
from .health import router as health_router
from .test import router as test_router
from .tools import router as tools_router

__all__ = ["chat_router", "health_router", "test_router", "tools_router"]
