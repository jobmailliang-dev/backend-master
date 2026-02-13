"""SSE 流式响应处理模块。"""

import asyncio
import json
from typing import AsyncGenerator


class SSEStreamer:
    """SSE 流式响应生成器。"""

    @staticmethod
    async def stream_content(content: str) -> str:
        """生成 content 事件。"""
        return f"event: content\ndata: {content}\n\n"

    @staticmethod
    async def stream_tool_call(tool_call: dict) -> str:
        """生成 tool_call 事件。"""
        return f"event: tool_call\ndata: {json.dumps(tool_call)}\n\n"

    @staticmethod
    async def stream_error(message: str) -> str:
        """生成 error 事件。"""
        error_data = {"message": message}
        return f"event: error\ndata: {json.dumps(error_data)}\n\n"

    @staticmethod
    async def stream_done() -> str:
        """生成 done 事件（流结束）。"""
        return "event: done\ndata:\n\n"

    @staticmethod
    async def generate_stream(message: str, client) -> AsyncGenerator[str, None]:
        """生成完整的 SSE 流。

        Args:
            message: 用户消息
            client: LLMClient 实例
        """
        try:
            # 发送用户消息到 LLM，获取流式响应
            response = client.chat(message)

            # 注意：由于当前 LLMClient 不支持流式输出，
            # 这里先返回完整响应，未来可扩展为真正的流式
            if response:
                # 模拟流式效果，逐字发送
                for char in response:
                    yield await SSEStreamer.stream_content(char)
                    # 短暂延迟模拟流式效果
                    await asyncio.sleep(0.01)

            yield await SSEStreamer.stream_done()

        except Exception as e:
            yield await SSEStreamer.stream_error(str(e))
            yield await SSEStreamer.stream_done()
