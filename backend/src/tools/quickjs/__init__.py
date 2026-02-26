"""QuickJS 工具模块。"""

import os

# 禁用 quickjs 的 assertion，避免 Proxy 对象序列化时的内部崩溃
os.environ.setdefault('QUICKJS_NO_ASSERT', '1')

from src.tools.quickjs.dict_proxy import DictProxy, DictProxyManager
from src.tools.quickjs.quickjs_tool import QuickJSTool

__all__ = ["QuickJSTool", "DictProxy", "DictProxyManager"]
