"""工具业务实体模块"""

from dataclasses import dataclass, field
from typing import Optional, List
import json
import sqlite3


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    description: str
    type: str  # 'string' | 'number' | 'boolean' | 'array' | 'object'
    required: bool = False
    default: Optional[str] = None
    enum: Optional[List[str]] = None
    hasEnum: bool = False  # 是否有枚举值

    def to_dict(self) -> dict:
        """转换为字典"""
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
        """从字典创建"""
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
    def from_json(cls, json_str: str) -> "ToolParameter":
        """从 JSON 字符串创建"""
        return cls.from_dict(json.loads(json_str))

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())


@dataclass
class Tool:
    """工具业务实体"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    is_active: bool = True
    parameters_json: str = "[]"  # JSON 序列化的参数列表
    inherit_from: Optional[str] = None
    code: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def parameters(self) -> List[ToolParameter]:
        """获取参数列表"""
        if not self.parameters_json:
            return []
        try:
            params_data = json.loads(self.parameters_json)
            return [ToolParameter.from_dict(p) for p in params_data]
        except (json.JSONDecodeError, TypeError):
            return []

    @parameters.setter
    def parameters(self, value: List[ToolParameter]):
        """设置参数列表"""
        self.parameters_json = json.dumps([p.to_dict() for p in value])

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "parameters": [p.to_dict() for p in self.parameters],
            "inherit_from": self.inherit_from,
            "code": self.code,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Tool":
        """从数据库行创建实体"""
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=bool(row["is_active"]) if row["is_active"] is not None else True,
            parameters_json=row["parameters_json"] or "[]",
            inherit_from=row["inherit_from"],
            code=row["code"] or "",
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
