"""工具业务实体模块"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, String, Text, Boolean, TIMESTAMP, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, TEXT

from ..datasource.database import Base


class ToolParameterType(TypeDecorator):
    """自定义类型：将 List[ToolParameter] 存储为 JSON，读取时自动转换回对象列表"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """写入数据库时：将 List[ToolParameter] 转换为 JSON 字符串"""
        if value and isinstance(value, list):
            if isinstance(value[0], ToolParameter):
                return json.dumps([asdict(p) for p in value], ensure_ascii=False)
        return json.dumps(value or [], ensure_ascii=False)

    def process_result_value(self, value, dialect):
        """从数据库读取时：将 JSON 字符串转换回 List[ToolParameter]"""
        if value:
            data_list = json.loads(value)
            return [ToolParameter.from_dict(d) for d in data_list]
        return []


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    description: str
    type: str  # 'string' | 'number' | 'boolean' | 'array' | 'object'
    required: bool = False
    default: Optional[str] = None
    enum: Optional[List[str]] = None
    hasEnum: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "required": self.required,
            "default": self.default,
            "enum": self.enum,
            "hasEnum": self.hasEnum
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ToolParameter":
        return cls(
            name=data["name"],
            description=data["description"],
            type=data["type"],
            required=data.get("required", False),
            default=data.get("default"),
            enum=data.get("enum"),
            hasEnum=data.get("hasEnum", False)
        )

    @classmethod
    def from_list(cls, data_list: List[dict]) -> List["ToolParameter"]:
        """从字典列表创建 ToolParameter 列表"""
        return [cls.from_dict(d) for d in data_list]

    @staticmethod
    def to_list(params: List["ToolParameter"]) -> List[dict]:
        """将 ToolParameter 列表转换为字典列表"""
        return [p.to_dict() for p in params]


@dataclass
class Tool(Base):
    """工具实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "tools"

    # 数据库字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parameters: Mapped[List[ToolParameter]] = mapped_column(ToolParameterType, default=list)
    inherit_from: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "parameters": ToolParameter.to_list(self.parameters or []),
            "inherit_from": self.inherit_from,
            "code": self.code,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
