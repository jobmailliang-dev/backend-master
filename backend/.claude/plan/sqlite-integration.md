# SQLite 数据库集成规划

## 1. 目标定义

为 LLM CLI V4 后端项目建立 SQLite 数据库框架接入点，实现简单的 `Test` 实体模型，使用 **injector** 框架通过 `@inject` 注解实现依赖注入，演示模块化的业务对象与服务类的层级关系。

### 1.1 核心目标

| 目标 | 描述 | 优先级 |
|------|------|--------|
| 数据源模块 | 新增 `src/modules/datasource/` 模块，提供数据库连接管理 | P0 |
| Test 模块 | 创建 `src/modules/test/` 模块，包含 Test 实体的 DAO、Service、Models | P0 |
| 依赖注入 | 集成 **injector** 框架，使用 `@inject` 注解实现依赖注入 | P1 |
| 测试验证 | 单文件测试 `tests/__test_test_module.py`，验证 service 层 | P0 |

---

## 2. 技术选型

### 2.1 依赖注入框架：injector

**安装**: `pip install injector`

| 特性 | 说明 |
|------|------|
| 注解方式 | `@inject` 装饰器 |
| 单例支持 | `scope=singleton` |
| 配置方式 | `Module` + `Binder` |
| 框架无关 | 可在任何 Python 项目使用 |
| 类型提示 | 完全支持 |

---

## 3. 架构设计

### 3.1 模块目录结构

```
src/
├── __main__.py
├── modules/
│   ├── __init__.py              # 模块注册 + Injector 初始化
│   │
│   ├── datasource/              # 数据源模块（共享基础设施）
│   │   ├── __init__.py
│   │   ├── connection.py       # 数据库连接管理
│   │   └── database.py         # 数据库初始化
│   │
│   └── test/                    # Test 功能模块
│       ├── __init__.py         # 模块导出
│       ├── models.py           # 业务对象 (Test)
│       ├── dao.py             # 数据访问对象 (TestDao)
│       └── service.py         # 服务层 (TestService)
│
├── api/
│   ├── __init__.py
│   └── test.py                # Test API 端点
│
├── core/                        # 核心业务逻辑
├── tools/                       # 工具系统
└── skills/                      # 技能系统
```

### 3.2 层级调用链

```
┌─────────────────────────────────────────────────────────┐
│                      API Layer                          │
│                   (src/api/test.py)                    │
│  - @inject 注入 TestService                             │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   TestService                           │
│  (src/modules/test/service.py)                         │
│  - @inject 注入 TestDao                                 │
│  - 单例模式 (scope=singleton)                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     TestDao                             │
│  (src/modules/test/dao.py)                             │
│  - @inject 注入 Connection                             │
│  - 单例模式 (scope=singleton)                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Connection                           │
│  (src/modules/datasource/connection.py)                │
│  - 单例模式 (scope=singleton)                           │
└────────────────────────────────------------------------─┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                       SQLite                            │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 详细设计

### 4.1 数据源模块 (`src/modules/datasource/`)

#### 4.1.1 连接管理 (`connection.py`)

```python
"""数据库连接管理模块"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Any


class Connection:
    """数据库连接包装类"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

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

    def execute(self, sql: str, params: tuple = ()) -> Any:
        """执行单条 SQL"""
        with self.transaction() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid

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
```

#### 4.1.2 数据库初始化 (`database.py`)

```python
"""数据库初始化模块"""

from .connection import Connection


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "data/app.db"):
        self._connection = Connection(db_path)
        self._initialized = False

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
```

### 4.2 Test 模块 (`src/modules/test/`)

#### 4.2.1 业务对象 (`models.py`)

```python
"""Test 业务实体模块"""

from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Test:
    """Test 业务实体"""
    id: Optional[int] = None
    name: str = ""
    value: str = ""
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Test":
        """从数据库行创建实体"""
        return cls(
            id=row["id"],
            name=row["name"],
            value=row["value"],
            created_at=row["created_at"]
        )
```

#### 4.2.2 DAO 层 (`dao.py`)

```python
"""Test 数据访问对象模块"""

from typing import Optional, List
from injector import inject
from .models import Test
from ..datasource.connection import Connection


class TestDao:
    """Test 数据访问对象"""

    TABLE_NAME = "test"

    @inject
    def __init__(self, connection: Connection):
        self.conn = connection

    def insert(self, test: Test) -> int:
        """插入记录，返回新记录的 ID"""
        sql = f"""
            INSERT INTO {self.TABLE_NAME} (name, value)
            VALUES (?, ?)
        """
        return self.conn.execute(sql, (test.name, test.value))

    def find_by_id(self, id: int) -> Optional[Test]:
        """根据 ID 查询"""
        sql = f"""
            SELECT id, name, value, created_at
            FROM {self.TABLE_NAME}
            WHERE id = ?
        """
        row = self.conn.query_one(sql, (id,))
        return Test.from_row(row) if row else None

    def find_all(self) -> List[Test]:
        """查询所有记录"""
        sql = f"""
            SELECT id, name, value, created_at
            FROM {self.TABLE_NAME}
            ORDER BY created_at DESC
        """
        rows = self.conn.query_all(sql)
        return [Test.from_row(row) for row in rows]

    def update(self, test: Test) -> bool:
        """更新记录"""
        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET name = ?, value = ?
            WHERE id = ?
        """
        result = self.conn.execute(sql, (test.name, test.value, test.id))
        return result > 0

    def delete(self, id: int) -> bool:
        """删除记录"""
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE id = ?"
        result = self.conn.execute(sql, (id,))
        return result > 0
```

#### 4.2.3 服务层 (`service.py`)

```python
"""Test 服务模块"""

from typing import Optional, List
from injector import inject
from .models import Test
from .dao import TestDao


class TestService:
    """Test 服务类 - 封装业务逻辑"""

    @inject
    def __init__(self, dao: TestDao):
        self.dao = dao

    def create(self, name: str, value: str) -> Test:
        """创建 Test 实体"""
        test = Test(name=name, value=value)
        test.id = self.dao.insert(test)
        return test

    def get_by_id(self, id: int) -> Optional[Test]:
        """获取 Test 实体"""
        return self.dao.find_by_id(id)

    def list_all(self) -> List[Test]:
        """列出所有 Test 实体"""
        return self.dao.find_all()

    def update(self, id: int, name: str, value: str) -> Optional[Test]:
        """更新 Test 实体"""
        test = self.dao.find_by_id(id)
        if not test:
            return None
        test.name = name
        test.value = value
        self.dao.update(test)
        return test

    def delete(self, id: int) -> bool:
        """删除 Test 实体"""
        return self.dao.delete(id)
```

#### 4.2.4 模块导出 (`__init__.py`)

```python
"""Test 功能模块"""

from .models import Test
from .service import TestService
from .dao import TestDao

__all__ = ["Test", "TestService", "TestDao"]
```

### 4.3 模块索引 + DI 配置 (`src/modules/__init__.py`)

```python
"""功能模块注册 - 依赖注入配置"""

from injector import Injector, Module, singleton
from injector import Binder

from .datasource import Connection, DatabaseManager
from .test import Test, TestService, TestDao


class DatabaseModule(Module):
    """数据库模块配置"""

    def configure(self, binder: Binder):
        # 连接 - 单例
        binder.bind(
            Connection,
            to=Connection("data/app.db"),
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


# 创建 Injector 实例
injector = Injector([
    DatabaseModule(),
    TestModule()
])

# 便捷函数
def get_injector() -> Injector:
    """获取 Injector 实例"""
    return injector


def get_test_service() -> TestService:
    """获取 TestService 实例"""
    return injector.get(TestService)


__all__ = [
    "injector",
    "get_injector",
    "get_test_service",
    "Test",
    "TestService",
    "TestDao",
    "Connection",
    "DatabaseManager"
]
```

---

## 5. API 端点使用示例

### 5.1 API 端点 (`src/api/test.py`)

```python
"""Test API 端点 - 使用 @inject 注解"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.modules import TestService, Test, get_injector

router = APIRouter(prefix="/api/test", tags=["test"])

# 获取 Injector 实例
_injector = get_injector()


@router.get("/health")
async def test_health():
    """健康检查"""
    return {"status": "ok", "module": "test"}


@router.post("/", response_model=dict)
async def create_test(request: dict):
    """创建 Test 记录 - 通过 Injector 获取服务"""
    # 从 Injector 获取 TestService（单例）
    service: TestService = _injector.get(TestService)

    test = service.create(request.get("name"), request.get("value"))
    return test.to_dict()


@router.get("/", response_model=List[dict])
async def list_tests():
    """列出所有 Test 记录"""
    service: TestService = _injector.get(TestService)
    tests = service.list_all()
    return [test.to_dict() for test in tests]


@router.get("/{test_id}", response_model=dict)
async def get_test(test_id: int):
    """获取单个 Test 记录"""
    service: TestService = _injector.get(TestService)
    test = service.get_by_id(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return test.to_dict()


@router.put("/{test_id}", response_model=dict)
async def update_test(test_id: int, request: dict):
    """更新 Test 记录"""
    service: TestService = _injector.get(TestService)
    test = service.update(test_id, request.get("name"), request.get("value"))
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    return test.to_dict()


@router.delete("/{test_id}")
async def delete_test(test_id: int):
    """删除 Test 记录"""
    service: TestService = _injector.get(TestService)
    success = service.delete(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"message": "Test deleted successfully"}
```

### 5.2 API 端点注解方式（备选）

```python
"""API 端点 - 类级别 @inject 注入"""

from fastapi import FastAPI
from injector import inject

class TestController:
    @inject
    def __init__(self, service: TestService):
        self.service = service

    def create(self, name: str, value: str):
        return self.service.create(name, value)

    def list_all(self):
        return self.service.list_all()


# 在 FastAPI 中使用
def create_test(name: str, value: str):
    controller = TestController()
    return controller.create(name, value)
```

---

## 6. 测试用例 (`tests/__test_test_module.py`)

```python
"""Test 模块集成测试 - 使用 Injector 获取服务"""

import pytest
import tempfile
import os

from src.modules import injector, Test, TestService, TestDao
from src.modules.datasource import Connection, DatabaseManager
from src.modules.test import TestDao, TestService


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # 创建临时数据库
        conn = Connection(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        yield conn
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def test_service(temp_db):
    """创建 TestService 实例 - 手动注入依赖"""
    dao = TestDao(connection=temp_db)
    return TestService(dao=dao)


class TestTestService:
    """TestService 单元测试"""

    def test_create(self, test_service):
        """测试创建 Test 实体"""
        test = test_service.create("test_001", "Hello World")
        assert test.id is not None
        assert test.name == "test_001"
        assert test.value == "Hello World"

    def test_get_by_id(self, test_service):
        """测试根据 ID 查询"""
        created = test_service.create("test_002", "Value 002")
        retrieved = test_service.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "test_002"

    def test_get_by_id_not_found(self, test_service):
        """测试查询不存在的 ID"""
        result = test_service.get_by_id(99999)
        assert result is None

    def test_list_all(self, test_service):
        """测试列出所有实体"""
        test1 = test_service.create("list_001", "A")
        test2 = test_service.create("list_002", "B")
        test3 = test_service.create("list_003", "C")

        all_tests = test_service.list_all()
        assert len(all_tests) >= 3

    def test_update(self, test_service):
        """测试更新实体"""
        created = test_service.create("update_001", "Original")
        updated = test_service.update(created.id, "Updated", "New Value")

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.value == "New Value"

    def test_delete(self, test_service):
        """测试删除实体"""
        created = test_service.create("delete_001", "To Delete")
        test_id = created.id

        result = test_service.delete(test_id)
        assert result is True

        retrieved = test_service.get_by_id(test_id)
        assert retrieved is None

    def test_singleton_behavior(self):
        """验证 Injector 单例模式"""
        # 从 Injector 获取两次服务
        service1 = injector.get(TestService)
        service2 = injector.get(TestService)

        # 验证是同一实例
        assert service1 is service2

    def test_dao_singleton(self):
        """验证 DAO 单例"""
        dao1 = injector.get(TestDao)
        dao2 = injector.get(TestDao)
        assert dao1 is dao2
```

---

## 7. 实施步骤

### 阶段一：依赖添加

| 步骤 | 任务 | 产出文件 |
|------|------|----------|
| 1.1 | 添加 injector 依赖 | `requirements.txt` 添加 `injector` |

### 阶段二：模块开发

| 步骤 | 任务 | 产出文件 |
|------|------|----------|
| 2.1 | 创建 modules 目录 | `src/modules/` |
| 2.2 | 实现 datasource 模块 | `src/modules/datasource/connection.py`, `database.py` |
| 2.3 | 实现 test 模块 - Models | `src/modules/test/models.py` |
| 2.4 | 实现 test 模块 - DAO | `src/modules/test/dao.py` |
| 2.5 | 实现 test 模块 - Service | `src/modules/test/service.py` |
| 2.6 | 编写模块初始化 + DI 配置 | `src/modules/__init__.py`, `src/modules/test/__init__.py` |

### 阶段三：API 端点

| 步骤 | 任务 | 产出文件 |
|------|------|----------|
| 3.1 | 创建 API 端点 | `src/api/test.py` |
| 3.2 | 注册路由 | `src/api/__init__.py` |

### 阶段四：测试

| 步骤 | 任务 | 产出文件 |
|------|------|----------|
| 4.1 | 创建测试文件 | `tests/__test_test_module.py` |
| 4.2 | 运行测试 | `pytest tests/__test_test_module.py` |

### 阶段五：验证

| 步骤 | 任务 | 产出文件 |
|------|------|----------|
| 5.1 | 验证测试通过 | 100% 通过 |
| 5.2 | 更新 CLAUDE.md | 添加模块文档 |

---

## 8. 验收标准

### 8.1 架构验收

- [ ] `injector` 成功集成
- [ ] `@inject` 注解正常工作
- [ ] 单例模式生效（Service、DAO、Connection）
- [ ] `src/modules/datasource/` 提供数据库连接
- [ ] `src/modules/test/` 包含完整的 Test 功能

### 8.2 功能验收

- [ ] SQLite 数据库可正常创建和连接
- [ ] Test 实体可正常 CRUD 操作
- [ ] Service 层测试全部通过

### 8.3 测试验收

| 测试项 | 预期结果 |
|--------|----------|
| test_create | 通过 |
| test_get_by_id | 通过 |
| test_get_by_id_not_found | 通过 |
| test_list_all | 通过 |
| test_update | 通过 |
| test_delete | 通过 |
| test_singleton_behavior | 通过 |
| test_dao_singleton | 通过 |
| **整体通过率** | **100%** |

---

## 9. 扩展新模块示例

新增 `User` 模块只需添加：

```
src/modules/user/
├── __init__.py    # 模块导出
├── models.py      # User 实体
├── dao.py         # UserDao (@inject connection)
└── service.py     # UserService (@inject dao)
```

注册到 Injector（在 `src/modules/__init__.py`）：

```python
from injector import Module, Binder

from .user import User, UserService, UserDao

class UserModule(Module):
    def configure(self, binder: Binder):
        binder.bind(UserDao, scope=singleton)
        binder.bind(UserService, scope=singleton)

# 添加到 Injector
injector = Injector([
    DatabaseModule(),
    TestModule(),
    UserModule()  # 新增
])
```

---

## 10. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| DI 框架 | injector | `@inject` 注解、单例支持、框架无关 |
| 数据库 | SQLite | 轻量、无需额外服务器 |
| 测试框架 | pytest | Python 社区标准 |

---

## 11. 使用示例

### 11.1 注解方式（推荐）

```python
"""Service 中使用 @inject 注入 DAO"""

from injector import inject

class TestService:
    @inject
    def __init__(self, dao: TestDao):  # 自动注入
        self.dao = dao

# 使用时无需手动传入 DAO
service = TestService()  # Injector 自动解析
```

### 11.2 获取服务实例

```python
"""从 Injector 获取服务"""

from src.modules import injector, TestService

# 获取 TestService（单例）
service: TestService = injector.get(TestService)

# 使用
test = service.create("name", "value")
```

### 11.3 API 中使用

```python
"""API 端点中获取服务"""

from src.modules import get_injector

_injector = get_injector()

@router.get("/")
async def list_items():
    service: TestService = _injector.get(TestService)
    return service.list_all()
```

---

## 12. 依赖文件更新

### requirements.txt

```
# 新增
injector>=1.0.0
```
