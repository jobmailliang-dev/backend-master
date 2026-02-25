"""工具业务实体模块"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, String, Text, Boolean, TIMESTAMP, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..datasource.database import Base


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


@dataclass
class Tool(Base):
    """工具实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "tools"

    # 数据库字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
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
            "parameters": self.parameters_json,
            "inherit_from": self.inherit_from,
            "code": self.code,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
