"""Test 业务实体模块"""

from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Test:
    """Test 业务实体"""
    id: Optional[int] = None
    name: str = ""
    value: str = ""
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Test":
        """从数据库行创建实体"""
        return cls(
            id=row["id"],
            name=row["name"],
            value=row["value"],
            created_at=row["created_at"]
        )
