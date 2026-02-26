"""对话和消息数据访问层 - SQLAlchemy 2.0 混合模式"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from injector import inject
from sqlalchemy.orm import Session


from .models import Conversation, Message


class ConversationDao:
    """对话数据访问对象"""

    @inject
    def __init__(self, session: Session):
        self._session = session

    def create(self, conversation: Conversation) -> str:
        """创建对话"""
        self._session.add(conversation)
        self._session.commit()
        return conversation.id

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据 ID 获取对话"""
        return self._session.get(Conversation, conversation_id)

    def get_all(self, user_id: str = "") -> List[Conversation]:
        """获取所有对话（按更新时间倒序）"""
        query = self._session.query(Conversation)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return query.order_by(Conversation.update_time.desc()).all()

    def update(self, conversation: Conversation) -> bool:
        """更新对话"""
        orm = self._session.get(Conversation, conversation.id)
        if not orm:
            return False
        orm.title = conversation.title
        orm.preview = conversation.preview
        orm.update_time = conversation.update_time
        orm.message_count = conversation.message_count
        orm.meta_data = conversation.meta_data
        self._session.commit()
        return True

    def delete(self, conversation_id: str) -> bool:
        """删除对话"""
        orm = self._session.get(Conversation, conversation_id)
        if not orm:
            return False
        self._session.delete(orm)
        self._session.commit()
        return True


class MessageDao:
    """消息数据访问对象"""

    @inject
    def __init__(self, session: Session):
        self._session = session

    def create(self, message: Message) -> str:
        """创建消息"""
        self._session.add(message)
        self._session.commit()
        return message.id

    def get_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """获取对话的所有消息（按时间正序）"""
        return (
            self._session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .all()
        )

    def delete_by_conversation_id(self, conversation_id: str) -> int:
        """删除对话的所有消息"""
        count = (
            self._session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .delete()
        )
        self._session.commit()
        return count

    def count_by_conversation_id(self, conversation_id: str) -> int:
        """获取对话的消息数量"""
        return (
            self._session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """根据 ID 获取消息"""
        return self._session.get(Message, message_id)

    def update_content(self, message_id: str, content: str) -> bool:
        """更新消息内容"""
        orm = self._session.get(Message, message_id)
        if not orm:
            return False
        orm.content = content
        self._session.commit()
        return True
