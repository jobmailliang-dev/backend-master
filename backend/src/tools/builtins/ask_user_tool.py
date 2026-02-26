"""AskUser 工具。

需要用户提供信息，当缺少 API Key、路径配置等时使用此工具。
"""

import json
import time
import uuid
from typing import Any, Dict

from src.tools.base import BaseTool
from src.utils.stream_writer_util import send_queue
from src.core.session_context import get_session


def generate_ask_user_id() -> str:
    """生成 ask_user 消息唯一ID"""
    now = time.time()
    now_str = str(int(now * 1000))
    rand = uuid.uuid4().hex[:6]
    return f"ask_{now_str}_{rand}"


class AskUserTool(BaseTool):
    """AskUser 工具。

    需要用户提供信息，当缺少 API Key、路径配置等时使用此工具。
    """

    def __init__(self):
        """初始化 AskUser 工具。"""
        super().__init__(
            name="ask_user",
            description="需要用户提供信息，当缺少 API Key、路径配置等时使用此工具。"
            "示例：{\"questions\": [{\"id\": \"api_key\", \"text\": \"请提供 API Key\", "
            "\"type\": \"text\", \"required\": true}], \"status\": \"PENDING\", "
            "\"next_task\": \"查询xxx\", \"title\": \"请填写信息\"}",
        )

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "description": "问题列表，每个为 {id, text, type, options?, required?}",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "问题 ID"},
                            "text": {"type": "string", "description": "问题文本"},
                            "type": {"type": "string", "description": "输入类型"},
                            "options": {
                                "type": "array",
                                "description": "选项列表",
                                "items": {"type": "string"},
                            },
                            "required": {"type": "boolean", "description": "是否必填"},
                        },
                        "required": ["id", "text", "type"],
                    },
                },
                "status": {
                    "type": "string",
                    "description": "对话框状态: PENDING(等待) 或 FINISH(完成)",
                    "enum": ["FINISH", "PENDING"],
                    "default": "PENDING",
                },
                "next_task": {
                    "type": "string",
                    "description": "下一个任务描述",
                },
                "question": {
                    "type": "string",
                    "description": "问题标题",
                },
            },
            "required": ["questions", "next_task", "question"],
        }

    def invoke(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具，向用户请求信息。

        Args:
            questions: 问题列表
            status: 状态 (PENDING/FINISH)
            next_task: 下一个任务描述
            question: 问题标题

        Returns:
            返回给用户的信息
        """
        questions = kwargs.get("questions", [])
        status = kwargs.get("status", "PENDING")
        next_task = kwargs.get("next_task", "")
        question = kwargs.get("question", "")

        # 生成 message_id 并保存消息到数据库
        session = get_session()
        message_id = None
        if session and hasattr(session, '_message_store') and session._message_store:
            message_id = generate_ask_user_id()
            content = json.dumps(kwargs, ensure_ascii=False)
            session._message_store.save_ask_user(message_id, content)

        # 将 message_id 加入推送参数
        if message_id:
            kwargs["message_id"] = message_id

        # 推送 SSE 事件到前端
        send_queue(kwargs, "ask_user")

        if status == "FINISH":
            return {
                "status": "FINISH",
                "message": "信息已提交完成",
            }

        return {
            "status": "PENDING",
            "message": f"已经通知用户,当前结束对话,不回复任何内容,回复""",
            "questions": questions,
            "next_task": next_task,
            "question": question,
        }

    def __repr__(self) -> str:
        return f"AskUserTool(name={self.name})"
