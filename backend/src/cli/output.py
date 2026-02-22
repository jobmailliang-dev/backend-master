"""输出格式化。

处理输出格式和美化。
"""

from typing import Any, Callable, Dict

from src.utils.stream_writer_util import send_queue


# 事件类型常量
EVENT_THINKING = "thinking"
EVENT_CONTENT = "content"
EVENT_TOOL_CALL = "tool_call"
EVENT_TOOL_RESULT = "tool_result"
EVENT_TOOL_ERROR = "tool_error"
EVENT_DONE = "done"
EVENT_ERROR = "error"


def print_welcome(title: str = "LLM CLI - Chat with AI", exit_cmd: str = "exit") -> None:
    """打印欢迎信息。"""
    print("=" * 60)
    print(f"{title}")
    print("=" * 60)
    print(f"Type '{exit_cmd}' to quit")
    print()


def print_thinking(content: str = "Thinking...") -> None:
    """在实时输出前打印状态信息（用于 CLI 打字机效果），灰色显示。"""
    send_queue({"content": content}, EVENT_THINKING)
    print(f"\x1b[90m[Thinking]  {content}\x1b[0m", end="", flush=True)


def print_message(content: str) -> None:
    """打印消息。"""
    send_queue({"content": content}, EVENT_CONTENT)
    print(content)


def print_error(message: str) -> None:
    """打印错误信息。"""
    send_queue({"message": message}, EVENT_ERROR)
    print(f"Error: {message}")


def print_tool_error(message: str) -> None:
    """打印工具错误信息。"""
    send_queue({"message": message}, EVENT_TOOL_ERROR)
    from src.tools.registry import get_registry
    get_registry().print_tool_error(message)


def print_tool_call(iteration: int, name: str, args: Dict[str, Any]) -> None:
    """打印工具调用信息。"""
    send_queue({"iteration": iteration, "name": name, "args": args}, EVENT_TOOL_CALL)
    from src.tools.registry import get_registry
    get_registry().print_tool_call(iteration, name, args)


def print_tool_result(name: str, result: str) -> None:
    """打印工具执行结果。"""
    send_queue({"name": name, "result": result}, EVENT_TOOL_RESULT)
    from src.tools.registry import get_registry
    get_registry().print_tool_result(name, result)


# 兼容旧代码：保留函数签名但不生效
def set_event_callback(callback: Callable[[str, Any], None]) -> None:
    """已废弃，保留兼容。"""
    pass


event_callback: Callable[[str, Any], None] = None

