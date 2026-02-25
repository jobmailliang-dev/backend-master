"""消息存储接口。

定义消息持久化的抽象接口。
"""

from typing import Any, Dict, List, Optional, runtime_checkable, Protocol


@runtime_checkable
class IMessageStore(Protocol):
    """消息存储接口"""

    def load_messages(self) -> List[Dict[str, Any]]:
        """加载历史消息

        Returns:
            消息列表，每条消息包含 role, content 等字段
        """
        ...

    def save_message(
        self,
        role: str,
        content: str,
        **kwargs: Any
    ) -> None:
        """保存消息

        Args:
            role: 角色 (user/assistant/tool)
            content: 消息内容
            **kwargs: 额外参数 (如 tool_call_id)
        """
        ...

    def load_metadata(self) -> Dict[str, Any]:
        """加载对话元数据

        Returns:
            元数据字典
        """
        ...
