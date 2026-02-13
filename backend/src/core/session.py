"""会话管理。

维护对话历史和消息状态。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import pytz


@dataclass
class Message:
    """单条消息。"""
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')).isoformat())
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为 API 消息格式。"""
        result = {"role": self.role, "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


class SessionManager:
    """会话管理器。"""

    def __init__(self, system_message: str, metadata: Dict[str, str] = None):
        """初始化会话。"""
        self.messages: List[Message] = []
        self._system_message = system_message
        self._metadata = metadata or {}
        self._init_system_message()

    def _init_system_message(self) -> None:
        """初始化系统消息。"""
        metadata_str = self._format_metadata()
        full_system = f"""{self._system_message}
---
## System Metadata
{metadata_str}"""

        self.messages.insert(0, Message(role="system", content=full_system))

    def _format_metadata(self) -> str:
        """格式化元数据。"""
        import re
        lines = []
        for key, value in self._metadata.items():
            # 替换 {time} 为当前时间
            if '{time}' in str(value):
                current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
                value = str(value).replace('{time}', current_time)
            lines.append(f"- {key}: {value}")
        return '\n'.join(lines)

    def add_user(self, content: str) -> None:
        """添加用户消息。"""
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str, tool_calls: List[Dict[str, Any]] = None) -> None:
        """添加助手消息。"""
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls or []))

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        """添加工具结果消息。"""
        self.messages.append(Message(role="tool", content=content, tool_call_id=tool_call_id))

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取所有消息（API 格式）。"""
        return [msg.to_dict() for msg in self.messages]

    def clear(self) -> None:
        """清空会话（保留系统消息）。"""
        system_msg = self.messages[0] if self.messages else None
        self.messages = []
        if system_msg:
            self.messages.append(system_msg)

    def get_history_count(self) -> int:
        """获取对话历史数量（不含系统消息）。"""
        return len([m for m in self.messages if m.role in ('user', 'assistant')])
