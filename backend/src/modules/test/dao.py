"""Test 数据访问对象模块 - SQLAlchemy 2.0 混合模式"""

from typing import Optional, List

from injector import inject
from sqlalchemy.orm import Session

from .models import Test


class TestDao:
    """Test 数据访问对象"""

    @inject
    def __init__(self, session: Session):
        self._session = session

    def insert(self, test: Test) -> int:
        """插入记录，返回新记录的 ID"""
        self._session.add(test)
        self._session.commit()
        return test.id

    def find_by_id(self, id: int) -> Optional[Test]:
        """根据 ID 查询"""
        return self._session.get(Test, id)

    def find_all(self) -> List[Test]:
        """查询所有记录"""
        return self._session.query(Test).order_by(Test.created_at.desc()).all()

    def update(self, test: Test) -> bool:
        """更新记录"""
        if not test.id:
            return False
        orm = self._session.get(Test, test.id)
        if not orm:
            return False
        orm.name = test.name
        orm.value = test.value
        self._session.commit()
        return True

    def delete(self, id: int) -> bool:
        """删除记录"""
        orm = self._session.get(Test, id)
        if not orm:
            return False
        self._session.delete(orm)
        self._session.commit()
        return True
