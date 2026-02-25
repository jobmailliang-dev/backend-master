"""对话和消息业务实体模块"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session


@dataclass
class Conversation:
    """对话业务实体"""
    id: str = ""
    user_id: str = ""
    title: str = "新对话"
    preview: str = ""
    create_time: int = 0
    update_time: int = 0
    message_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "userId": self.user_id,
            "title": self.title,
            "preview": self.preview,
            "createTime": self.create_time,
            "updateTime": self.update_time,
            "messageCount": self.message_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_orm(cls, orm_obj) -> "Conversation":
        """从 ORM 对象创建实体"""
        if orm_obj is None:
            return None
        metadata = {}
        if orm_obj.metadata:
            try:
                metadata = json.loads(orm_obj.metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        return cls(
            id=orm_obj.id,
            user_id=orm_obj.user_id or "",
            title=orm_obj.title or "新对话",
            preview=orm_obj.preview or "",
            create_time=orm_obj.create_time,
            update_time=orm_obj.update_time,
            message_count=orm_obj.message_count or 0,
            metadata=metadata
        )

    # 兼容旧版 sqlite3.Row
    @classmethod
    def from_row(cls, row) -> "Conversation":
        """从数据库行创建实体"""
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            preview=row["preview"] or "",
            create_time=row["create_time"],
            update_time=row["update_time"],
            message_count=row["message_count"] or 0,
            metadata=metadata
        )


@dataclass
class Message:
    """消息业务实体"""
    id: str = ""
    conversation_id: str = ""
    role: str = "user"  # user | assistant
    content: str = ""
    timestamp: int = 0
    tool_calls: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "conversationId": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls
        }

    @classmethod
    def from_orm(cls, orm_obj) -> "Message":
        """从 ORM 对象创建实体"""
        if orm_obj is None:
            return None
        tool_calls = []
        if orm_obj.tool_calls:
            try:
                tool_calls = json.loads(orm_obj.tool_calls)
            except (json.JSONDecodeError, TypeError):
                tool_calls = []
        return cls(
            id=orm_obj.id,
            conversation_id=orm_obj.conversation_id,
            role=orm_obj.role,
            content=orm_obj.content,
            timestamp=orm_obj.timestamp,
            tool_calls=tool_calls
        )

    # 兼容旧版 sqlite3.Row
    @classmethod
    def from_row(cls, row) -> "Message":
        """从数据库行创建实体"""
        tool_calls = []
        if row["tool_calls"]:
            try:
                tool_calls = json.loads(row["tool_calls"])
            except (json.JSONDecodeError, TypeError):
                tool_calls = []
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            timestamp=row["timestamp"],
            tool_calls=tool_calls
        )
