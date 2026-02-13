"""Test 模块集成测试 - 使用 Injector 获取服务"""

import pytest
import tempfile
import os

from src.modules import injector, Test, TestService, TestDao
from src.modules.datasource import Connection, DatabaseManager


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # 创建临时数据库
        conn = Connection(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        yield conn
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def test_service(temp_db):
    """创建 TestService 实例 - 手动注入依赖"""
    dao = TestDao(connection=temp_db)
    return TestService(dao=dao)


class TestTestService:
    """TestService 单元测试"""

    def test_create(self, test_service):
        """测试创建 Test 实体"""
        test = test_service.create("test_001", "Hello World")
        assert test.id is not None
        assert test.name == "test_001"
        assert test.value == "Hello World"

    def test_get_by_id(self, test_service):
        """测试根据 ID 查询"""
        created = test_service.create("test_002", "Value 002")
        retrieved = test_service.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "test_002"

    def test_get_by_id_not_found(self, test_service):
        """测试查询不存在的 ID"""
        result = test_service.get_by_id(99999)
        assert result is None

    def test_list_all(self, test_service):
        """测试列出所有实体"""
        test1 = test_service.create("list_001", "A")
        test2 = test_service.create("list_002", "B")
        test3 = test_service.create("list_003", "C")

        all_tests = test_service.list_all()
        assert len(all_tests) >= 3

    def test_update(self, test_service):
        """测试更新实体"""
        created = test_service.create("update_001", "Original")
        updated = test_service.update(created.id, "Updated", "New Value")

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.value == "New Value"

    def test_delete(self, test_service):
        """测试删除实体"""
        created = test_service.create("delete_001", "To Delete")
        test_id = created.id

        result = test_service.delete(test_id)
        assert result is True

        retrieved = test_service.get_by_id(test_id)
        assert retrieved is None

    def test_singleton_behavior(self):
        """验证 Injector 单例模式"""
        # 从 Injector 获取两次服务
        service1 = injector.get(TestService)
        service2 = injector.get(TestService)

        # 验证是同一实例
        assert service1 is service2

    def test_dao_singleton(self):
        """验证 DAO 单例"""
        dao1 = injector.get(TestDao)
        dao2 = injector.get(TestDao)
        assert dao1 is dao2
