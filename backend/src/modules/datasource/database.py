"""数据库连接管理模块 - SQLAlchemy 2.0 版本"""

import os
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column


from sqlalchemy.orm import Session

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base"""
    pass


# 全局引擎和 Session 工厂
_engine = None
_SessionLocal = None


def _get_engine(db_path: str = "data/app.db"):
    """获取或创建数据库引擎"""
    global _engine
    if _engine is None:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        with _engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode = WAL")
            conn.exec_driver_sql("PRAGMA synchronous = NORMAL")
            conn.exec_driver_sql("PRAGMA busy_timeout = 5000")
            conn.exec_driver_sql("PRAGMA cache_size = -64000")
            conn.exec_driver_sql("PRAGMA foreign_keys = ON")
    return _engine


def get_engine(db_path: str = "data/app.db"):
    """获取或创建数据库引擎"""
    return _get_engine(db_path)


def get_session_local(db_path: str = "data/app.db"):
    """获取 Session 工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine(db_path))
    return _SessionLocal


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = self._load_db_path()
        self._engine = _get_engine(db_path)
        self._session_local = get_session_local(db_path)
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
    def session(self):
        return self._session_local()

    def create_all_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self._engine)

    def drop_all_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self._engine)

    def init_database(self):
        """初始化数据库表（仅执行一次）"""
        if self._initialized:
            return
        self.create_all_tables()
        self._initialized = True
