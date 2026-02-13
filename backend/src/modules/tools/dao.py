"""工具数据访问层"""

from typing import Optional, List
import sqlite3
from injector import inject
from .models import Tool
from ..datasource.connection import Connection


class ToolDao:
    """工具数据访问对象"""

    @inject
    def __init__(self, conn: Connection):
        self._conn = conn  # Connection 包装类
        self.create_table()

    def create_table(self):
        """创建工具表"""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                parameters_json TEXT DEFAULT '[]',
                inherit_from TEXT,
                code TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def create(self, tool: Tool) -> int:
        """创建工具"""
        sql = """
            INSERT INTO tools (name, description, is_active, parameters_json, inherit_from, code)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self._conn.execute(sql, (
            tool.name,
            tool.description,
            int(tool.is_active),
            tool.parameters_json,
            tool.inherit_from,
            tool.code
        ))

    def get_by_id(self, tool_id: int) -> Optional[Tool]:
        """根据 ID 获取工具"""
        row = self._conn.query_one("SELECT * FROM tools WHERE id = ?", (tool_id,))
        return Tool.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Tool]:
        """根据名称获取工具"""
        row = self._conn.query_one("SELECT * FROM tools WHERE name = ?", (name,))
        return Tool.from_row(row) if row else None

    def get_all(self) -> List[Tool]:
        """获取所有工具"""
        rows = self._conn.query_all("SELECT * FROM tools ORDER BY name")
        return [Tool.from_row(row) for row in rows]

    def get_active(self) -> List[Tool]:
        """获取所有启用的工具"""
        rows = self._conn.query_all("SELECT * FROM tools WHERE is_active = 1 ORDER BY name")
        return [Tool.from_row(row) for row in rows]

    def update(self, tool: Tool) -> bool:
        """更新工具"""
        if not tool.id:
            return False
        rowcount = self._conn.execute_update_delete("""
            UPDATE tools
            SET name = ?, description = ?, is_active = ?, parameters_json = ?,
                inherit_from = ?, code = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            tool.name,
            tool.description,
            int(tool.is_active),
            tool.parameters_json,
            tool.inherit_from,
            tool.code,
            tool.id
        ))
        return rowcount > 0

    def delete(self, tool_id: int) -> bool:
        """删除工具"""
        rowcount = self._conn.execute_update_delete("DELETE FROM tools WHERE id = ?", (tool_id,))
        return rowcount > 0

    def count(self) -> int:
        """获取工具总数"""
        row = self._conn.query_one("SELECT COUNT(*) FROM tools")
        return row[0] if row else 0
