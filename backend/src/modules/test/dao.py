"""Test 数据访问对象模块"""

from typing import Optional, List
from injector import inject
from .models import Test
from ..datasource.connection import Connection


class TestDao:
    """Test 数据访问对象"""

    TABLE_NAME = "test"

    @inject
    def __init__(self, connection: Connection):
        self.conn = connection

    def insert(self, test: Test) -> int:
        """插入记录，返回新记录的 ID"""
        sql = f"""
            INSERT INTO {self.TABLE_NAME} (name, value)
            VALUES (?, ?)
        """
        return self.conn.execute(sql, (test.name, test.value))

    def find_by_id(self, id: int) -> Optional[Test]:
        """根据 ID 查询"""
        sql = f"""
            SELECT id, name, value, created_at
            FROM {self.TABLE_NAME}
            WHERE id = ?
        """
        row = self.conn.query_one(sql, (id,))
        return Test.from_row(row) if row else None

    def find_all(self) -> List[Test]:
        """查询所有记录"""
        sql = f"""
            SELECT id, name, value, created_at
            FROM {self.TABLE_NAME}
            ORDER BY created_at DESC
        """
        rows = self.conn.query_all(sql)
        return [Test.from_row(row) for row in rows]

    def update(self, test: Test) -> bool:
        """更新记录"""
        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET name = ?, value = ?
            WHERE id = ?
        """
        result = self.conn.execute(sql, (test.name, test.value, test.id))
        return result > 0

    def delete(self, id: int) -> bool:
        """删除记录"""
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE id = ?"
        result = self.conn.execute_update_delete(sql, (id,))
        return result > 0
