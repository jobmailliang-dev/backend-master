"""Test 业务实体模块"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import String, TIMESTAMP, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..datasource.database import Base


@dataclass
class Test(Base):
    """Test 实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "test"

    # 数据库字段
    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
