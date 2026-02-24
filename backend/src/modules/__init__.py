"""功能模块注册 - Module 声明

本模块仅导出 Module 类定义，实际的 Injector 实例化在 core/injector.py 中。
"""

from injector import Module, singleton
from injector import Binder

from .datasource import Connection, DatabaseManager
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


class DatabaseModule(Module):
    """数据库模块配置"""

    def configure(self, binder: Binder):
        # 连接 - 单例，使用工厂函数确保目录创建

        def _init_database():
            """初始化数据库"""
            conn = Connection("data/app.db")
            conn.init_schema()
            return conn

        binder.bind(
            Connection,
            to=_init_database,
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
    "Connection",
    "DatabaseManager"
]
