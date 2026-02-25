"""对话和消息业务实体模块"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..datasource.database import Base


@dataclass
class Conversation(Base):
    """对话实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "conversations"

    # 数据库字段
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="新对话")
    preview: Mapped[str] = mapped_column(String, default="")
    create_time: Mapped[int] = mapped_column(Integer)
    update_time: Mapped[int] = mapped_column(Integer)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[str] = mapped_column(Text, default="{}")

    # 业务属性（非数据库字段）
    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """获取 metadata 为字典"""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    @metadata_dict.setter
    def metadata_dict(self, value: Dict[str, Any]):
        self.metadata = json.dumps(value) if value else "{}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "title": self.title,
            "preview": self.preview,
            "createTime": self.create_time,
            "updateTime": self.update_time,
            "messageCount": self.message_count,
            "metadata": self.metadata_dict
        }


@dataclass
class Message(Base):
    """消息实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "messages"

    # 数据库字段
    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[int] = mapped_column(Integer)
    tool_calls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 业务属性（非数据库字段）
    @property
    def tool_calls_list(self) -> List[Any]:
        """获取 tool_calls 为列表"""
        if not self.tool_calls:
            return []
        try:
            return json.loads(self.tool_calls)
        except (json.JSONDecodeError, TypeError):
            return []

    @tool_calls_list.setter
    def tool_calls_list(self, value: List[Any]):
        self.tool_calls = json.dumps(value) if value else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversationId": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls_list
        }
