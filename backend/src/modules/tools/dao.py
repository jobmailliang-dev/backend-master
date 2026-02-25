"""工具数据访问层 - SQLAlchemy 2.0 混合模式"""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

from injector import inject

from sqlalchemy.orm import Session
from .models import Tool
    


class ToolDao:
    """工具数据访问对象"""

    @inject
    def __init__(self, session: Session):
        self._session = session

    def create(self, tool: Tool) -> int:
        """创建工具"""
        self._session.add(tool)
        self._session.commit()
        return tool.id

    def get_by_id(self, tool_id: int) -> Optional[Tool]:
        """根据 ID 获取工具"""
        return self._session.get(Tool, tool_id)

    def get_by_name(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        return self._session.query(Tool).filter(Tool.name == name).first()

    def get_all(self) -> List[Tool]:
        """获取所有工具"""
        return self._session.query(Tool).order_by(Tool.name).all()

    def get_active(self) -> List[Tool]:
        """获取所有启用的工具"""
        return self._session.query(Tool).filter(Tool.is_active == True).order_by(Tool.name).all()

    def update(self, tool: Tool) -> bool:
        """更新工具"""
        if not tool.id:
            return False
        orm = self._session.get(Tool, tool.id)
        if not orm:
            return False
        orm.name = tool.name
        orm.description = tool.description
        orm.is_active = tool.is_active
        orm.parameters = tool.parameters
        orm.inherit_from = tool.inherit_from
        orm.code = tool.code
        self._session.commit()
        return True

    def delete(self, tool_id: int) -> bool:
        """删除工具"""
        orm = self._session.get(Tool, tool_id)
        if not orm:
            return False
        self._session.delete(orm)
        self._session.commit()
        return True

    def count(self) -> int:
        """获取工具总数"""
        return self._session.query(Tool).count()
