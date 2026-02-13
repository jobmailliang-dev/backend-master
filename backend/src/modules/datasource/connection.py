"""数据库连接管理模块"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Any


class Connection:
    """数据库连接包装类"""

    def __init__(self, db_path: str = "data/app.db"):
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path

    def init_schema(self):
        """初始化数据库表"""
        self.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """事务上下文管理器"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = (), return_rowcount: bool = False) -> Any:
        """执行单条 SQL

        Args:
            sql: SQL 语句
            params: 参数
            return_rowcount: 是否返回受影响行数（用于 UPDATE/DELETE）
        """
        with self.transaction() as conn:
            cursor = conn.execute(sql, params)
            if return_rowcount:
                return cursor.rowcount
            return cursor.lastrowid

    def execute_update_delete(self, sql: str, params: tuple = ()) -> int:
        """执行 UPDATE 或 DELETE，返回受影响行数"""
        return self.execute(sql, params, return_rowcount=True)

    def query_one(self, sql: str, params: tuple = ()) -> Any:
        """查询单条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()

    def query_all(self, sql: str, params: tuple = ()) -> list:
        """查询多条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchall()
