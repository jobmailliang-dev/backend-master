"""流式写入工具。

提供 SSE (Server-Sent Events) 流式写入的异步任务支持。
用于在异步任务中安全地将数据推送到流式响应队列。

主要组件:
- MyStreamWriter: 线程安全的流写入器
- send_queue: 向流写入事件
- create_queue_task: 创建异步任务并返回队列
- task_context: 任务上下文 ContextVar
"""

import asyncio
import json
from contextvars import ContextVar
from typing import Any, Callable, Awaitable, TypeVar, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 泛型返回值类型
R = TypeVar("R")

# 任务上下文，使用 ContextVar 跨协程传递
# 使用 default=dict 而非 default={}，避免可变默认对象导致的上下文污染
task_context: ContextVar[dict[str, Any]] = ContextVar('task_context', default=dict)


def send_queue(msg: Any, event: str) -> None:
    """向流写入事件数据。

    Args:
        msg: 要发送的消息数据
        event: 事件名称，如 "content", "done", "error" 等
    """
    try:
        context = task_context.get()
        logger.warning(f"context:::: {context}")
        if not context:
            return
        writer = context.get("stream_writer")
        if writer is None:
            return
        # 字符串直接发送，否则 JSON 序列化（ensure_ascii=False 保留中文）
        data = msg if isinstance(msg, str) else json.dumps(msg, ensure_ascii=False)
        writer.write(f"event: {event}\ndata: {data}\n\n")
    except Exception as e:
        logger.warning(f"发送队列消息失败: {str(e)}")


def create_queue_task(
    func: Callable[..., Awaitable[R]],
    *args,
    context_data: Optional[dict[str, Any]] = None,
    **kwargs
) -> asyncio.Queue:
    """创建一个异步任务并返回队列。

    用于在异步任务中执行长时间运行的操作，并通过队列
    将执行过程中的状态/结果流式返回给调用方。

    Args:
        func: 异步函数
        *args: 传递给 func 的位置参数
        context_data: 可选的额外上下文数据，会被合并到 task_context 中
        **kwargs: 传递给 func 的关键字参数

    Returns:
        asyncio.Queue 对象，可用于获取任务执行过程中的数据

    Example:
        ```python
        async def long_running_task():
            for i in range(5):
                await asyncio.sleep(1)
                send_queue({"progress": i}, "progress")

        queue = create_queue_task(long_running_task)

        async def consume():
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk

        # 使用 context_data 传递额外上下文
        queue = create_queue_task(task_func, context_data={"conversation_id": "123"})
        # 在任务中可以通过 task_context.get()["conversation_id"] 获取
        ```
    """
    queue = asyncio.Queue()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    writer = MyStreamWriter(queue, loop)

    async def callback(stream_writer: MyStreamWriter) -> None:
        """内部回调函数，执行异步任务并管理上下文。

        使用显式 set/reset 确保每个任务有独立的上下文，避免上下文污染。
        """
        # 显式创建新上下文并设置，确保任务间隔离
        context: dict[str, Any] = {}
        token = task_context.set(context)
        try:
            context["stream_writer"] = stream_writer
            # 合并额外的上下文数据（如 conversation_id）
            if context_data:
                context.update(context_data)
            # 执行工具
            await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"异步任务执行失败: {str(e)}")
        finally:
            task_context.reset(token)
            stream_writer.close()  # 确保最后关闭流

    # 当前事件循环中启动协程
    asyncio.create_task(callback(writer))
    return queue


class MyStreamWriter:
    """线程安全的流写入器。

    用于在异步任务中安全地写入数据到队列，支持线程安全操作。

    Attributes:
        queue: asyncio 队列实例
        loop: 事件循环引用
    """

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        """初始化流写入器。

        Args:
            queue: asyncio 队列实例
            loop: 事件循环引用
        """
        self.queue = queue
        self.loop = loop

    def write(self, msg: Any) -> None:
        """同步方法：供深层嵌套的逻辑调用。

        使用 call_soon_threadsafe 确保即使在线程池中运行也能安全推入队列。

        Args:
            msg: 要写入队列的消息
        """
        logger.info(msg)
        self.loop.call_soon_threadsafe(self.queue.put_nowait, msg)

    def close(self) -> None:
        """标记传输结束。

        向队列写入 None 信号，表示数据传输完成。
        """
        self.loop.call_soon_threadsafe(self.queue.put_nowait, None)


__all__ = [
    'send_queue',
    'create_queue_task',
    'MyStreamWriter',
    'task_context',
]
