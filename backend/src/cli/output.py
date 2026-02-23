"""输出格式化。

处理输出格式和美化。
"""

import json
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.theme import Theme

from src.utils.stream_writer_util import send_queue


# 事件类型常量
EVENT_THINKING = "thinking"
EVENT_CONTENT = "content"
EVENT_TOOL_CALL = "tool_call"
EVENT_TOOL_RESULT = "tool_result"
EVENT_TOOL_ERROR = "tool_error"
EVENT_DONE = "done"
EVENT_ERROR = "error"


# ==================== 打印机类 ====================


class BasePrinter(ABC):
    """输出打印机抽象基类"""

    @abstractmethod
    def print_welcome(self, title: str, exit_cmd: str) -> None:
        pass

    @abstractmethod
    def print_thinking(self, content: str) -> None:
        pass

    @abstractmethod
    def print_message(self, content: str) -> None:
        pass

    @abstractmethod
    def print_error(self, message: str) -> None:
        pass

    @abstractmethod
    def print_tool_call(self, iteration: int, name: str, args: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def print_tool_result(self, name: str, result: str) -> None:
        pass

    @abstractmethod
    def print_tool_error(self, error_msg: str) -> None:
        pass


class SimplePrinter(BasePrinter):
    """简单打印机 - 纯文本输出"""

    def __init__(self):
        self.gray = "\033[90m" if sys.stdout.isatty() else ""
        self.reset = "\033[0m" if sys.stdout.isatty() else ""

    def print_welcome(self, title: str, exit_cmd: str) -> None:
        print("=" * 60)
        print(f"{title}")
        print("=" * 60)
        print(f"Type '{exit_cmd}' to quit")
        print()
        print("提示：Ctrl+Enter 换行，Enter 发送，Ctrl+C 退出")

    def print_thinking(self, content: str) -> None:
        print(f"\x1b[90m[Thinking]  {content}\x1b[0m", end="", flush=True)

    def print_message(self, content: str) -> None:
        print(content)

    def print_error(self, message: str) -> None:
        print(f"Error: {message}")

    def print_tool_call(self, iteration: int, name: str, args: Dict[str, Any]) -> None:
        args_str = str(args)
        print(f"\n{self.gray}[Tool Call #{iteration}] {self.reset}"
              f"{self.gray}{name} {self.reset}with args: {self.gray}{args_str}{self.reset}")

    def print_tool_result(self, name: str, result: str) -> None:
        result_str = str(result)
        max_len = 500
        if len(result_str) > max_len:
            result_str = result_str[:max_len] + "..."
        print(f"{self.gray}[Tool Result] {self.reset}"
              f"{self.gray}{name}: {result_str}{self.reset}\n")

    def print_tool_error(self, error_msg: str) -> None:
        print(f"{self.gray}[Tool Error] {self.reset}"
              f"{self.gray}{error_msg}{self.reset}\n")


class ConsolePrinter(BasePrinter):
    """Rich 控制台打印机 - 美化输出"""

    def __init__(self):
        custom_theme = Theme({
            "repr.str": "cyan",
            "repr.number": "green",
            "repr.bool": "yellow",
        })
        self.console = Console(theme=custom_theme)

    def print_welcome(self, title: str, exit_cmd: str) -> None:
        """打印欢迎面板"""
        self.console.print(Panel(
            f"[bold cyan]{title}[/bold cyan]\n\n"
            f"Type '[yellow]{exit_cmd}[/yellow]' to quit\n\n"
            f"[dim]提示：Ctrl+Enter 换行，Enter 发送，Ctrl+C 退出[/dim]",
            title="[bold green]Welcome[/bold green]",
            border_style="green",
            expand=False
        ))

    def print_thinking(self, content: str) -> None:
        """打印思考状态"""
        with self.console.status("[dim]Thinking...[/dim]", spinner="dots") as status:
            status.update(content)

    def print_message(self, content: str) -> None:
        """打印消息，支持 Markdown 渲染，带边框"""
        try:
            md = Markdown(content)
            self.console.print(Panel(
                md,
                title="[bold]Assistant[/bold]",
                border_style="blue",
                expand=True
            ))
        except Exception:
            self.console.print(Panel(
                content,
                title="[bold]Assistant[/bold]",
                border_style="blue",
                expand=True
            ))

    def print_error(self, message: str) -> None:
        """打印错误信息"""
        self.console.print(Panel(
            f"[bold red]{message}[/bold red]",
            title="Error", border_style="red", expand=False
        ))

    def print_tool_call(self, iteration: int, name: str, args: Dict[str, Any]) -> None:
        """打印工具调用信息"""
        args_str = json.dumps(args, ensure_ascii=False, indent=2)
        syntax = Syntax(args_str, "json", theme="monokai", line_numbers=False,word_wrap=True)
        self.console.print(Panel(
            syntax,
            title=f"[bold cyan]Tool Call #{iteration}[/bold cyan] {name}",
            border_style="cyan", expand=True
        ))

    def print_tool_result(self, name: str, result: str) -> None:
        """打印工具执行结果"""
        result_str = str(result)
        max_len = 500
        if len(result_str) > max_len:
            result_str = result_str[:max_len] + "\n... (truncated)"
        try:
            parsed = json.loads(result_str)
            syntax = Syntax(json.dumps(parsed, ensure_ascii=False, indent=2), "json", theme="monokai", word_wrap=True)
            border_style = "green"
        except (json.JSONDecodeError, TypeError):
            syntax = result_str
            border_style = "blue"
        self.console.print(Panel(
            syntax,
            title=f"[bold green]Tool Result[/bold green] {name}",
            border_style=border_style, expand=True
        ))

    def print_tool_error(self, error_msg: str) -> None:
        """打印工具错误信息"""
        self.console.print(Panel(
            f"[bold red]{error_msg}[/bold red]",
            title="[bold]Tool Error[/bold]", border_style="red", expand=False
        ))


# 全局打印机实例
_simple_printer = SimplePrinter()
_console_printer = ConsolePrinter()
_current_printer: BasePrinter = _simple_printer


def set_printer_mode(mode: str) -> None:
    """设置打印机模式: simple / rich"""
    global _current_printer
    _current_printer = _console_printer if mode == "rich" else _simple_printer


def get_printer() -> BasePrinter:
    """获取当前打印机实例"""
    return _current_printer


# ==================== 现有函数（保留签名，修改实现） ====================


def print_welcome(title: str = "LLM CLI - Chat with AI", exit_cmd: str = "exit") -> None:
    """打印欢迎信息。"""
    get_printer().print_welcome(title, exit_cmd)


def print_thinking(content: str = "Thinking...") -> None:
    """在实时输出前打印状态信息（用于 CLI 打字机效果），灰色显示。"""
    send_queue({"content": content}, EVENT_THINKING)
    get_printer().print_thinking(content)


def print_message(content: str) -> None:
    """打印消息。"""
    send_queue({"content": content}, EVENT_CONTENT)
    get_printer().print_message(content)


def print_error(message: str) -> None:
    """打印错误信息。"""
    send_queue({"message": message}, EVENT_ERROR)
    get_printer().print_error(message)


def print_tool_call(iteration: int, name: str, args: Dict[str, Any]) -> None:
    """打印工具调用信息。"""
    send_queue({"iteration": iteration, "name": name, "args": args}, EVENT_TOOL_CALL)
    get_printer().print_tool_call(iteration, name, args)


def print_tool_result(name: str, result: str) -> None:
    """打印工具执行结果。"""
    send_queue({"name": name, "result": result}, EVENT_TOOL_RESULT)
    get_printer().print_tool_result(name, result)


def print_tool_error(message: str) -> None:
    """打印工具错误信息。"""
    send_queue({"message": message}, EVENT_TOOL_ERROR)
    get_printer().print_tool_error(message)
