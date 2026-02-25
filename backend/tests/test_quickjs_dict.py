"""QuickJS dict 代理功能测试。"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from src.tools.quickjs.dict_proxy import DictProxy, DictProxyManager
from src.tools.quickjs.quickjs_tool import QuickJSTool


class TestDictProxy:
    """DictProxy 单元测试。"""

    def test_basic_get_set(self):
        """测试基础读写。"""
        data = {"name": "Alice", "age": 30}
        proxy = DictProxy(data)

        assert proxy.get("name") == "Alice"
        assert proxy.get("age") == 30

        proxy.set("name", "Bob")
        assert data["name"] == "Bob"

    def test_nested_dict(self):
        """测试嵌套 dict。"""
        data = {"user": {"name": "Alice", "age": 30}}
        proxy = DictProxy(data)

        user_proxy = proxy.get("user")
        assert isinstance(user_proxy, DictProxy)
        assert user_proxy.get("name") == "Alice"

    def test_list_handling(self):
        """测试列表处理。"""
        data = {"skills": ["Python", "JS"]}
        proxy = DictProxy(data)

        skills = proxy.get("skills")
        assert skills == ["Python", "JS"]

    def test_keys_and_has(self):
        """测试键操作。"""
        data = {"name": "Alice", "age": 30}
        proxy = DictProxy(data)

        assert proxy.has("name") is True
        assert proxy.has("gender") is False
        assert set(proxy.keys()) == {"name", "age"}

    def test_delete(self):
        """测试删除操作。"""
        data = {"name": "Alice", "age": 30}
        proxy = DictProxy(data)

        assert proxy.delete("age") is True
        assert "age" not in data
        assert proxy.delete("nonexistent") is False

    def test_to_dict(self):
        """测试获取原始 dict。"""
        data = {"name": "Alice"}
        proxy = DictProxy(data)

        result = proxy.to_dict()
        assert result is data  # 应该是同一个引用


class TestDictProxyManager:
    """DictProxyManager 单元测试。"""

    def test_create_and_get(self):
        """测试创建和获取代理。"""
        manager = DictProxyManager()

        data = {"key": "value"}
        obj_id = manager.create(data, "test")

        assert obj_id == "test"
        assert manager.get(obj_id) is not None
        assert manager.get(obj_id).to_dict() == data

    def test_get_by_dict(self):
        """测试通过原始 dict 获取代理。"""
        manager = DictProxyManager()

        data = {"key": "value"}
        obj_id = manager.create(data, "test")

        proxy = manager.get_by_dict(data)
        assert proxy is not None
        assert proxy.obj_id == "test"

    def test_release(self):
        """测试释放代理。"""
        manager = DictProxyManager()

        data = {"key": "value"}
        obj_id = manager.create(data, "test")

        assert manager.release(obj_id) is True
        assert manager.get(obj_id) is None

    def test_clear(self):
        """测试清空所有代理。"""
        manager = DictProxyManager()

        manager.create({"a": 1}, "a")
        manager.create({"b": 2}, "b")

        manager.clear()
        assert len(manager.list_ids()) == 0


class TestQuickJSToolDict:
    """QuickJSTool dict 暴露功能集成测试。"""

    def test_expose_dict_basic(self):
        """测试基础 dict 暴露。"""
        tool = QuickJSTool()

        my_data = {"name": "Alice", "age": 30}
        var_name = tool.expose_dict(my_data, "userData")

        assert var_name == "userData"

        # JS 读取
        result = tool.invoke(code="userData.name")
        assert result["result"] == "Alice"

    def test_expose_dict_write(self):
        """测试 JS 写入修改 Python。"""
        tool = QuickJSTool()

        my_data = {"name": "Alice", "age": 30}
        tool.expose_dict(my_data, "userData")

        # JS 修改
        tool.invoke(code="userData.name = 'Bob'")

        # Python 获取修改
        assert my_data["name"] == "Bob"

    def test_expose_dict_add_key(self):
        """测试 JS 添加新键。"""
        tool = QuickJSTool()

        my_data = {"name": "Alice"}
        tool.expose_dict(my_data, "userData")

        # JS 添加新键
        tool.invoke(code="userData.city = 'Beijing'")

        assert my_data.get("city") == "Beijing"

    def test_expose_dict_nested(self):
        """测试嵌套 dict。"""
        tool = QuickJSTool()

        my_data = {"user": {"name": "Alice", "age": 30}}
        tool.expose_dict(my_data, "data")

        # JS 修改嵌套属性
        tool.invoke(code="data.user.name = 'Bob'")

        assert my_data["user"]["name"] == "Bob"

    def test_get_dict(self):
        """测试获取原始 dict。"""
        tool = QuickJSTool()

        my_data = {"name": "Alice"}
        tool.expose_dict(my_data, "userData")

        # 修改后再获取
        tool.invoke(code="userData.age = 30")

        result = tool.get_dict("userData")
        assert result == {"name": "Alice", "age": 30}

    def test_release_dict(self):
        """测试释放 dict。"""
        tool = QuickJSTool()

        my_data = {"name": "Alice"}
        tool.expose_dict(my_data, "userData")

        # 释放后应该无法访问
        tool.release_dict("userData")

        # 再次获取应该返回 None
        assert tool.get_dict("userData") is None

    def test_multiple_dicts(self):
        """测试多个 dict。"""
        tool = QuickJSTool()

        data1 = {"name": "Alice"}
        data2 = {"title": "Engineer"}

        var1 = tool.expose_dict(data1, "user")
        var2 = tool.expose_dict(data2, "job")

        assert var1 == "user"
        assert var2 == "job"

        tool.invoke(code="user.name = 'Bob'")
        tool.invoke(code="job.title = 'Manager'")

        assert data1["name"] == "Bob"
        assert data2["title"] == "Manager"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
