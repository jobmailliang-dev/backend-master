"""数据库初始化模块"""

import os
from .connection import Connection


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 从配置文件读取
            db_path = self._load_db_path()
        self._connection = Connection(db_path)
        self._initialized = False

    def _load_db_path(self) -> str:
        """从配置文件加载数据库路径"""
        try:
            import yaml
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, "config.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('database', {}).get('path', 'data/app.db')
        except Exception:
            pass
        return 'data/app.db'

    @property
    def conn(self) -> Connection:
        return self._connection

    def init_database(self):
        """初始化数据库表（仅执行一次）"""
        if self._initialized:
            return
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._initialized = True
