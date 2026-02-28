"""Dict 代理模块。

提供 DictProxy 类，用于将 Python dict 对象暴露给 QuickJS，
实现双向数据绑定。
"""

import threading
import uuid
from typing import Any, Dict, List, Optional


class DictProxy:
    """Python dict 代理类，用于暴露给 QuickJS。

    该类包装一个 Python dict 对象，提供 get/set 方法供 QuickJS 调用，
    从而实现 JS 对 Python dict 的修改能够同步回原始对象。
    """

    def __init__(self, data: dict, obj_id: str = None):
        """初始化代理。

        Args:
            data: 要代理的 Python dict 对象
            obj_id: 唯一标识符，默认使用对象 id
        """
        self._data = data
        self._obj_id = obj_id or f"dict_{id(data)}"
        # 缓存子代理，避免重复创建
        self._children_cache: dict = {}

    def get(self, key: str) -> Any:
        """获取属性值。

        Args:
            key: 属性键

        Returns:
            属性值，如果是 dict 会递归包装为 DictProxy
        """
        value = self._data.get(key)
        # 使用 id(value) 作为缓存键，确保同一对象返回相同代理
        cache_key = id(value) if isinstance(value, (dict, list)) else key
        if cache_key in self._children_cache:
            return self._children_cache[cache_key]
        result = self._wrap_value(value)
        if cache_key != key:
            self._children_cache[cache_key] = result
        return result

    def set(self, key: str, value: Any) -> None:
        """设置属性值。

        Args:
            key: 属性键
            value: 要设置的值
        """
        self._data[key] = self._unwrap_value(value)

    def delete(self, key: str) -> bool:
        """删除属性。

        Args:
            key: 属性键

        Returns:
            是否成功删除
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def keys(self) -> List[str]:
        """获取所有键。

        Returns:
            键列表
        """
        return list(self._data.keys())

    def has(self, key: str) -> bool:
        """检查键是否存在。

        Args:
            key: 属性键

        Returns:
            键是否存在
        """
        return key in self._data

    def to_dict(self) -> dict:
        """返回原始 dict 引用。

        Returns:
            原始 Python dict 对象
        """
        return self._data

    @property
    def obj_id(self) -> str:
        """获取代理对象 ID。"""
        return self._obj_id

    def _wrap_value(self, value: Any) -> Any:
        """将 Python 值包装为可代理的形式。

        Args:
            value: Python 值

        Returns:
            包装后的值，dict 会转为 DictProxy
        """
        if isinstance(value, dict):
            # 使用唯一 ID 生成子代理 ID，避免键名冲突
            child_id = f"{self._obj_id}.child_{id(value)}"
            return DictProxy(value, child_id)
        if isinstance(value, list):
            return [self._wrap_value(item) for item in value]
        return value

    def _unwrap_value(self, value: Any) -> Any:
        """将 JS 传入的值转换为 Python 对象。

        Args:
            value: JS 传入的值

        Returns:
            转换后的 Python 对象
        """
        if isinstance(value, DictProxy):
            return value.to_dict()
        if isinstance(value, dict):
            # 处理 JS 对象（包含 __proxy_id 的情况）
            if "__proxy_id" in value:
                # 这是一个嵌套的代理引用
                return value
            # 递归处理普通 dict
            return {k: self._unwrap_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._unwrap_value(item) for item in value]
        return value


class DictProxyManager:
    """管理多个 DictProxy 实例的生命周期。"""

    def __init__(self):
        """初始化管理器。"""
        self._proxies: Dict[str, DictProxy] = {}
        self._reverse_ref: Dict[int, str] = {}  # id(py_dict) -> obj_id
        self._lock = threading.Lock()  # 线程锁

    def create(self, py_dict: dict, name: str = None) -> str:
        """创建新的代理。

        Args:
            py_dict: 要代理的 Python dict
            name: 可选的名称

        Returns:
            代理的 obj_id
        """
        with self._lock:
            if name:
                obj_id = name
            else:
                # 使用 UUID 确保唯一性
                obj_id = f"dict_{uuid.uuid4().hex[:8]}"
            proxy = DictProxy(py_dict, obj_id)
            self._proxies[obj_id] = proxy
            self._reverse_ref[id(py_dict)] = obj_id
            return obj_id

    def get(self, obj_id: str) -> Optional[DictProxy]:
        """获取代理实例。

        Args:
            obj_id: 代理 ID

        Returns:
            DictProxy 实例，不存在返回 None
        """
        return self._proxies.get(obj_id)

    def get_by_dict(self, py_dict: dict) -> Optional[DictProxy]:
        """通过原始 dict 获取代理。

        Args:
            py_dict: 原始 Python dict

        Returns:
            DictProxy 实例，不存在返回 None
        """
        obj_id = self._reverse_ref.get(id(py_dict))
        return self._proxies.get(obj_id) if obj_id else None

    def release(self, obj_id: str) -> bool:
        """释放代理。

        Args:
            obj_id: 代理 ID

        Returns:
            是否成功释放
        """
        if obj_id in self._proxies:
            proxy = self._proxies[obj_id]
            # 移除反向引用
            dict_id = id(proxy.to_dict())
            if dict_id in self._reverse_ref:
                del self._reverse_ref[dict_id]
            del self._proxies[obj_id]
            return True
        return False

    def clear(self) -> None:
        """清空所有代理。"""
        self._proxies.clear()
        self._reverse_ref.clear()

    def list_ids(self) -> List[str]:
        """列出所有代理 ID。"""
        return list(self._proxies.keys())
