"""聊天 API 路由。"""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core import get_app_config, LLMClient
from src.cli.output import EVENT_DONE, EVENT_ERROR
from src.utils.stream_writer_util import create_queue_task, send_queue
from src.modules import MessageService
from src.core import injector

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 全局客户端实例
_client: Optional[LLMClient] = None
_injector = injector


def get_message_service() -> MessageService:
    """获取 MessageService 实例"""
    return _injector.get(MessageService)


def get_client() -> LLMClient:
    """获取或创建 LLM 客户端实例。"""
    global _client
    if _client is None:
        config = get_app_config()
        _client = LLMClient(
            llm_config=config.llm,
            tools_config=config.tools,
            metadata=config.get_system_metadata_dict()
        )
    return _client


class ChatRequest(BaseModel):
    """聊天请求体。"""
    message: str


class ChatResponse(BaseModel):
    """聊天响应。"""
    success: bool
    response: str
    tool_calls: Optional[list] = None


@router.post("")
async def chat(request: ChatRequest) -> ChatResponse:
    """同步聊天接口。"""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        client = get_client()
        response = client.chat(request.message)
        return ChatResponse(
            success=True,
            response=response,
            tool_calls=None  # 可扩展获取工具调用历史
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call LLM API: {str(e)}")


async def _run_chat_stream(message: str, conversation_id: Optional[str] = None) -> None:
    """运行 chat 并通过 send_queue 发送事件。"""
    full_response = ""
    try:
        client = get_client()

        # 如果有 conversation_id，先保存用户消息
        if conversation_id:
            try:
                msg_service = get_message_service()
                msg_service.create_message(conversation_id, "user", message)
            except Exception as e:
                print(f"保存用户消息失败: {e}")

        # 调用 chat，响应会通过内部的 print_message 函数发送（流式输出）
        full_response = await client.achat(message) or ""

    except Exception as e:
        send_queue({"message": str(e)}, EVENT_ERROR)
    finally:
        # 流结束时保存助手消息
        if conversation_id and full_response:
            try:
                msg_service = get_message_service()
                msg_service.create_message(conversation_id, "assistant", full_response)
            except Exception as e:
                print(f"保存助手消息失败: {e}")

        send_queue("", EVENT_DONE)


async def generate_sse_stream(message: str, conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """生成 SSE 流（实时推送）。"""
    queue = create_queue_task(_run_chat_stream, message, conversation_id)
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


@router.get("/stream")
async def chat_stream(
    message: str = Query(..., description="用户消息"),
    conversationId: Optional[str] = Query(default=None, description="对话ID")
):
    """SSE 流式聊天接口。"""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        generate_sse_stream(message, conversationId),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
