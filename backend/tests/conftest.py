"""工具模块测试配置"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import sqlite3
from pathlib import Path

# 测试数据库路径
TEST_DB_PATH = tempfile.mktemp(suffix=".db")


@pytest.fixture(scope="session")
def db_connection():
    """数据库连接 fixture"""
    conn = sqlite3.connect(TEST_DB_PATH)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """数据库游标 fixture"""
    cursor = db_connection.cursor()
    yield cursor
    # 每个测试后回滚
    cursor.connection.rollback()


@pytest.fixture
def app():
    """FastAPI 应用 fixture"""
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

    from src.api.tools import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    return app


@pytest.fixture
def client(app):
    """测试客户端 fixture"""
    return TestClient(app)


@pytest.fixture
def sample_tool_data():
    """示例工具数据"""
    return {
        "name": "test_tool",
        "description": "测试工具描述",
        "is_active": True,
        "parameters": [
            {
                "name": "param1",
                "description": "参数1描述",
                "type": "string",
                "required": True
            }
        ],
        "code": "print('hello')"
    }


@pytest.fixture
def sample_tool_list():
    """示例工具列表"""
    return [
        {
            "name": "tool_1",
            "description": "工具1",
            "is_active": True,
            "parameters": [],
            "code": "code1"
        },
        {
            "name": "tool_2",
            "description": "工具2",
            "is_active": False,
            "parameters": [],
            "code": "code2"
        }
    ]
