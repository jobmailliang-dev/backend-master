"""对话和消息业务实体模块"""

from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Conversation:
    """对话业务实体"""
    id: str = ""
    title: str = "新对话"
    preview: str = ""
    create_time: int = 0
    update_time: int = 0
    message_count: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "preview": self.preview,
            "createTime": self.create_time,
            "updateTime": self.update_time,
            "messageCount": self.message_count
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Conversation":
        """从数据库行创建实体"""
        return cls(
            id=row["id"],
            title=row["title"],
            preview=row["preview"] or "",
            create_time=row["create_time"],
            update_time=row["update_time"],
            message_count=row["message_count"] or 0
        )


@dataclass
class Message:
    """消息业务实体"""
    id: str = ""
    conversation_id: str = ""
    role: str = "user"  # user | assistant
    content: str = ""
    timestamp: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "conversationId": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Message":
        """从数据库行创建实体"""
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            timestamp=row["timestamp"]
        )
