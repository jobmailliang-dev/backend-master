"""对话和消息业务实体模块"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import String, Text, Integer, ForeignKey, JSON, TIMESTAMP
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
    create_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    meta_data: Mapped[dict] = mapped_column("meta_data", JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "title": self.title,
            "preview": self.preview,
            "createTime": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else "",
            "updateTime": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else "",
            "messageCount": self.message_count,
            "meta_data": self.meta_data or {}
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
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversationId": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "tool_calls": self.tool_calls or [],
            "tool_call_id": self.tool_call_id
        }
