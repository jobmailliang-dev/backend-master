"""功能模块注册 - Module 声明

本模块仅导出 Module 类定义，实际的 Injector 实例化在 core/injector.py 中。
"""
from typing import Any, Type, TypeVar
from injector import Module, singleton
from injector import Binder
from sqlalchemy.orm import Session

from .datasource import DatabaseManager, get_session_local
from .test import Test, TestService, TestDao
from .tools import Tool, ToolService, ToolDao
from .conversations import (
    Conversation,
    Message,
    ConversationDao,
    MessageDao,
    ConversationService,
    MessageService
)

from injector import Injector, Module, singleton
T = TypeVar("T")


class DatabaseModule(Module):
    """数据库模块配置"""

    def configure(self, binder: Binder):
        # 初始化数据库
        def _init_database():
            """初始化数据库"""
            db_manager = DatabaseManager("data/app.db")
            db_manager.init_database()
            return db_manager

        binder.bind(
            DatabaseManager,
            to=_init_database,
            scope=singleton
        )

        # SQLAlchemy Session - 单例
        def _get_session() -> Session:
            """获取 SQLAlchemy Session"""
            session_local = get_session_local()
            return session_local()

        binder.bind(
            Session,
            to=_get_session,
            scope=singleton
        )


class TestModule(Module):
    """Test 模块配置"""

    def configure(self, binder: Binder):
        # DAO - 单例
        binder.bind(
            TestDao,
            scope=singleton
        )
        # Service - 单例
        binder.bind(
            TestService,
            scope=singleton
        )


class ToolModule(Module):
    """Tool 模块配置"""

    def configure(self, binder: Binder):
        # DAO - 单例
        binder.bind(
            ToolDao,
            scope=singleton
        )
        # Service - 单例
        binder.bind(
            ToolService,
            scope=singleton
        )


class ConversationModule(Module):
    """Conversation 模块配置"""

    def configure(self, binder: Binder):
        # DAO - 单例
        binder.bind(
            ConversationDao,
            scope=singleton
        )
        # Service - 单例
        binder.bind(
            ConversationService,
            scope=singleton
        )


class MessageModule(Module):
    """Message 模块配置"""

    def configure(self, binder: Binder):
        # DAO - 单例
        binder.bind(
            MessageDao,
            scope=singleton
        )
        # Service - 单例
        binder.bind(
            MessageService,
            scope=singleton
        )

# 创建全局 Injector 实例
injector: Injector = Injector([
    DatabaseModule(),
    TestModule(),
    ToolModule(),
    ConversationModule(),
    MessageModule(),
])


def reload_modules() -> None:
    """重新加载模块（用于测试或动态添加模块）"""
    global injector
    injector = Injector([
        DatabaseModule(),
        TestModule(),
        ToolModule(),
        ConversationModule(),
        MessageModule(),
    ])


def get_service(service_class: Type[T]) -> T:
    """从 Injector 获取服务实例。

    Args:
        service_class: 服务类类型

    Returns:
        服务实例

    Example:
        message_service = get_service(MessageService)
    """
    return injector.get(service_class)


__all__ = [
    "DatabaseModule",
    "TestModule",
    "ToolModule",
    "ConversationModule",
    "MessageModule",
    "Test",
    "TestService",
    "TestDao",
    "Tool",
    "ToolService",
    "ToolDao",
    "Conversation",
    "Message",
    "ConversationDao",
    "MessageDao",
    "ConversationService",
    "MessageService",
    "DatabaseManager"
]
