"""Session 上下文管理。

通过 ContextVar 在工具中获取当前会话的 session 对象。
"""

from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.session import SessionManager

# ContextVar 用于在线程/协程间传递 session 对象
_session_var: ContextVar[Optional["SessionManager"]] = ContextVar("session", default=None)


def set_session(session: "SessionManager") -> None:
    """设置当前线程/协程的 session 对象。

    Args:
        session: SessionManager 实例
    """
    _session_var.set(session)


def get_session() -> Optional["SessionManager"]:
    """获取当前线程/协程的 session 对象。

    Returns:
        SessionManager 实例，如果未设置则返回 None
    """
    return _session_var.get()


def clear_session() -> None:
    """清除 session 对象。"""
    _session_var.set(None)
