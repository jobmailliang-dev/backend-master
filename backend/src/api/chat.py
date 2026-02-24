"""聊天 API 路由。"""

from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core import get_app_config, LLMClient, IMessageStore
from src.cli.output import EVENT_DONE, EVENT_ERROR
from src.utils.stream_writer_util import create_queue_task, send_queue
from src.modules import MessageService
from src.modules.conversations import MessageStoreImpl
from src.core import injector

router = APIRouter(prefix="/api/chat", tags=["chat"])

_injector = injector


def get_message_service() -> MessageService:
    """获取 MessageService 实例"""
    return _injector.get(MessageService)


def create_client(message_store: Optional[IMessageStore] = None) -> LLMClient:
    """创建新的 LLM 客户端实例（每次请求创建新实例以保证线程安全）

    Args:
        message_store: 消息存储接口实现
    """
    config = get_app_config()
    return LLMClient(
        llm_config=config.llm,
        tools_config=config.tools,
        metadata=config.get_system_metadata_dict(),
        message_store=message_store,
    )


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
        client = create_client()
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
        # 创建消息存储实现（每次创建新实例）
        message_store: Optional[IMessageStore] = None
        if conversation_id:
            msg_service = get_message_service()
            message_store = MessageStoreImpl(msg_service, conversation_id)

        # 创建客户端，传入 message_store
        client = create_client(message_store=message_store)

        
        # 调用 chat，响应会通过内部的 print_message 函数发送（流式输出）
        # 注意：消息保存由 SessionManager 自动处理
        full_response = await client.achat(message) or ""

    except Exception as e:
        send_queue({"message": str(e)}, EVENT_ERROR)
    finally:
        send_queue("", EVENT_DONE)


async def generate_sse_stream(message: str, conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """生成 SSE 流（实时推送）。

    Args:
        message: 用户消息
        conversation_id: 对话ID，会被放入 task_context 中供其他模块获取
    """
    # 将 conversation_id 放入上下文，供其他地方通过 task_context.get()["conversation_id"] 获取
    context_data = {"conversation_id": conversation_id} if conversation_id else {}
    queue = create_queue_task(_run_chat_stream, message, conversation_id, context_data=context_data)
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
