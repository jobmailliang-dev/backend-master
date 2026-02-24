"""MessageService 的 IMessageStore 实现"""

from typing import Any, Dict, List, Optional

from src.core.message_store import IMessageStore
from src.modules.conversations import MessageService


class MessageStoreImpl(IMessageStore):
    """MessageService 的 IMessageStore 实现"""

    def __init__(self, message_service: MessageService, conversation_id: str):
        """初始化消息存储实现

        Args:
            message_service: MessageService 实例
            conversation_id: 对话 ID
        """
        self._message_service = message_service
        self._conversation_id = conversation_id

    def load_messages(self) -> List[Dict[str, Any]]:
        """从数据库加载历史消息"""
        messages = self._message_service.get_by_conversation_id(self._conversation_id)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
            }
            for msg in messages
        ]

    def save_message(
        self,
        role: str,
        content: str,
        **kwargs: Any
    ) -> None:
        """保存消息到数据库"""
        tool_calls = kwargs.get("tool_calls")
        self._message_service.create_message(self._conversation_id, role, content, tool_calls)
