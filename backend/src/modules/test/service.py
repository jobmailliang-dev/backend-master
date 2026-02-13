"""Test 服务模块"""

from typing import Optional, List
from injector import inject
from .models import Test
from .dao import TestDao


class TestService:
    """Test 服务类 - 封装业务逻辑"""

    @inject
    def __init__(self, dao: TestDao):
        self.dao = dao

    def create(self, name: str, value: str) -> Test:
        """创建 Test 实体"""
        test = Test(name=name, value=value)
        test.id = self.dao.insert(test)
        return test

    def get_by_id(self, id: int) -> Optional[Test]:
        """获取 Test 实体"""
        return self.dao.find_by_id(id)

    def list_all(self) -> List[Test]:
        """列出所有 Test 实体"""
        return self.dao.find_all()

    def update(self, id: int, name: str, value: str) -> Optional[Test]:
        """更新 Test 实体"""
        test = self.dao.find_by_id(id)
        if not test:
            return None
        test.name = name
        test.value = value
        self.dao.update(test)
        return test

    def delete(self, id: int) -> bool:
        """删除 Test 实体"""
        return self.dao.delete(id)
