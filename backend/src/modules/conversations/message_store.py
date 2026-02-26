"""MessageService 的 IMessageStore 实现"""

from typing import Any, Dict, List

from src.core.message_store import IMessageStore
from src.core.session_context import get_session
from src.modules.conversations import ConversationService, MessageService
from src.core import get_service


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
        self._conversation_service = get_service(ConversationService)

    # 大模型需要的角色类型
    VALID_ROLES = ("user", "assistant", "tool")

    def load_messages(self) -> List[Dict[str, Any]]:
        """从数据库加载历史消息"""
        messages = self._message_service.get_by_conversation_id(self._conversation_id)
        # 过滤只保留大模型需要的角色类型
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
            }
            for msg in messages
            if msg.role in self.VALID_ROLES
        ]

    def save_message(
        self,
        role: str,
        content: str,
        **kwargs: Any
    ) -> None:
        """保存消息到数据库"""
        tool_calls = kwargs.get("tool_calls")
        tool_call_id = kwargs.get("tool_call_id")

        # 获取 session 中的 metadata
        session = get_session()
        meta_data = session._metadata if session else None

        self._message_service.create_message(
            self._conversation_id, role, content, tool_calls, tool_call_id=tool_call_id, meta_data=meta_data
        )

    def load_metadata(self) -> Dict[str, Any]:
        """从数据库加载对话元数据"""
        conversation = self._conversation_service.get_one(self._conversation_id)
        if conversation:
            return conversation.meta_data
        return {}

    def save_ask_user(
        self,
        id: str,
        content: str,
    ) -> None:
        """保存 ask_user 消息到数据库

        Args:
            id: 消息 ID
            content: 消息内容 (JSON 字符串)
        """
        self._message_service.create_message(
            self._conversation_id,
            role="ask_user",
            content=content,
            tool_calls=[],
            tool_call_id=None,
            id=id,
        )
