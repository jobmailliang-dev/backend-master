"""聊天 API 路由。"""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.config.loader import load_config
from src.core.client import LLMClient
from src.cli.output import EVENT_DONE, EVENT_ERROR
from src.utils.stream_writer_util import create_queue_task, send_queue

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 全局客户端实例
_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    """获取或创建 LLM 客户端实例。"""
    global _client
    if _client is None:
        config = load_config()
        _client = LLMClient(
            openai_config=config.openai,
            tools_config=config.tools,
            llm_provider=config.llm_provider,
            qwen_config=config.qwen,
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


async def _run_chat_stream(message: str) -> None:
    """运行 chat 并通过 send_queue 发送事件。"""
    try:
        client = get_client()
        client.chat(message)
    except Exception as e:
        send_queue({"message": str(e)}, EVENT_ERROR)
    finally:
        send_queue("", EVENT_DONE)


async def generate_sse_stream(message: str) -> AsyncGenerator[str, None]:
    """生成 SSE 流（实时推送）。"""
    queue = create_queue_task(_run_chat_stream, message)
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


@router.get("/stream")
async def chat_stream(message: str = Query(..., description="用户消息")):
    """SSE 流式聊天接口。"""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        generate_sse_stream(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
