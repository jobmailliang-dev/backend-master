"""MessageService 的 IMessageStore 实现"""

from typing import Any, Dict, List

from src.core.message_store import IMessageStore
from src.modules.conversations import MessageService,ConversationDao
from src.core.injector import get_service


class MessageStoreImpl(IMessageStore):
    """MessageService 的 IMessageStore 实现"""

    def __init__(
        self,
        conversation_id: str,
    ):
        """初始化消息存储实现

        Args:
            conversation_id: 对话 ID
        """
        self._conversation_id = conversation_id
        self._message_service: MessageService = get_service(MessageService)
        self._conversation_dao = get_service(ConversationDao)

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
        print(f"save_message::: {content}")
        self._message_service.create_message(self._conversation_id, role, content, tool_calls)

    def load_metadata(self) -> Dict[str, Any]:
        """从数据库加载对话元数据"""
        conversation = self._conversation_dao.get_by_id(self._conversation_id)
        if conversation:
            return conversation.metadata
        return {}
