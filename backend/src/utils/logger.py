"""日志工具。

提供简单的日志封装。
"""

import sys
from typing import Optional


class Logger:
    """简单日志封装。"""

    _GRAY = "\033[90m" if sys.stdout.isatty() else ""
    _RESET = "\033[0m" if sys.stdout.isatty() else ""

    def __init__(self, name: str = "cli"):
        """初始化日志器。"""
        self.name = name
        self._quiet = False

    def set_quiet(self, quiet: bool) -> None:
        """设置安静模式。"""
        self._quiet = quiet

    def info(self, message: str) -> None:
        """输出信息日志。"""
        if not self._quiet:
            print(f"{self._GRAY}[INFO]{self._RESET} {message}")

    def error(self, message: str) -> None:
        """输出错误日志。"""
        print(f"{self._GRAY}[ERROR]{self._RESET} {message}")

    def debug(self, message: str) -> None:
        """输出调试日志。"""
        if not self._quiet:
            print(f"{self._GRAY}[DEBUG]{self._RESET} {message}")

    def warning(self, message: str) -> None:
        """输出警告日志。"""
        print(f"{self._GRAY}[WARNING]{self._RESET} {message}")


# 全局日志器
_global_logger: Optional[Logger] = None


def get_logger(name: str = "cli") -> Logger:
    """获取全局日志器。"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name)
    return _global_logger
