[根目录](../../CLAUDE.md) > [backend-master](../) > **backend**

# WIMI CHAT - 后端核心模块

This file provides guidance to Claude Code when working with code in this repository.

## 模块职责

Backend 模块是 WIMI CHAT 的核心后端服务，提供：

- **Web 服务**: FastAPI 服务，支持 SSE 流式响应
- **LLM 客户端**: 集成 OpenAI/Qwen 兼容 API，处理对话和工具调用
- **工具系统**: 可扩展的工具注册和执行框架
- **技能系统**: 动态加载和执行技能内容

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements.txt -r pyproject.toml[dev]  # 含开发依赖

# 运行
python -m src --web    # Web 模式（默认端口 8000）
python -m src --cli    # CLI 模式
python -m src --port 8080  # 指定端口

# 代码质量
black src/             # 格式化
isort src/             # 排序导入
flake8 src/            # 代码检查
```

## 对外接口

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat` | POST | 同步聊天 |
| `/api/chat/stream` | GET | SSE 流式聊天 |
| `/api/health` | GET | 健康检查 |
| `/api/tools` | GET/POST/PUT/DELETE | 工具管理 |

### SSE 事件

`content`, `tool_call`, `tool_result`, `tool_error`, `thinking`, `reasoning`, `done`, `error`

## 架构概览

```
src/
├── __main__.py           # 应用入口（CLI/Web 双模式）
├── api/                  # API 路由层
│   ├── chat.py           # 聊天 API（同步 + SSE）
│   ├── test.py           # 测试 API
│   ├── tools.py          # 工具管理 API
│   └── models.py         # 通用 API 响应模型（ApiResponse）
├── core/                 # 核心业务逻辑
│   ├── client.py         # LLM 客户端，处理工具调用循环
│   └── session.py        # 会话消息管理
├── modules/              # 业务模块（依赖注入）
│   ├── __init__.py       # 模块注册和注入器（Injector）
│   ├── base.py           # 基础接口（IService, ValidException）
│   ├── datasource/       # 数据库连接
│   ├── test/             # 测试模块（models.py, dao.py, service.py）
│   └── tools/            # 工具模块（models.py, dtos.py, dao.py, service.py）
├── tools/                # 工具执行系统
│   ├── registry.py       # 工具注册表
│   ├── base.py          # BaseTool 抽象基类
│   └── builtins/         # 内置工具
├── skills/               # 技能系统
├── adapters/             # LLM 适配器
├── config/               # 配置管理
├── utils/                # 通用工具
│   └── logger.py         # 日志配置
└── web/                  # Web 中间件
    ├── logging_middleware.py  # 请求日志中间件
    └── sse.py            # SSE 支持
```

## 添加新工具

1. 在 `src/tools/builtins/` 创建工具类，继承 `BaseTool`
2. 实现 `name`, `description`, `get_parameters()`, `execute()` 方法
3. 在 `src/tools/registry_init.py` 中注册

## 添加新技能

1. 在 `data/skills/` 创建目录，添加 `SKILL.md`
2. 包含 YAML frontmatter（name, description, license）
3. 使用 `{placeholder}` 占位符支持变量替换

## 添加新 LLM 适配器

1. 在 `src/adapters/` 创建适配器文件，如 `xxx.py`
2. 继承 `LLMAdapter` 抽象基类
3. 实现 `complete()`, `complete_stream()`, `complete_auto()` 方法
4. 在 `src/adapters/__init__.py` 中导出
5. 在 `src/config/models.py` 添加配置模型（如 `XxxConfig`）
6. 在 `src/config/loader.py` 添加解析函数
7. 在 `src/config/models.py` 的 `AppConfig` 中添加配置字段
8. 更新 `LLMClient.__init__()` 支持新的提供商

## 添加新 API 端点（业务模块）

项目采用 **DAO → Service → API** 三层架构，使用 **依赖注入** 管理服务生命周期。

### 目录结构

```
src/modules/xxx/
├── __init__.py          # 导出 XxxService, XxxDao, XxxDto, IXxxService
├── models.py            # 业务实体（dataclass）
├── dtos.py              # 数据传输对象（Pydantic BaseModel）
├── dao.py               # 数据访问层
└── service.py           # 服务层（接口 + 实现）
```

### 1. models.py - 业务实体层

使用 SQLAlchemy ORM 映射，继承 `Base` 类：

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, TIMESTAMP, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..datasource.database import Base


@dataclass
class XxxParameter:
    """参数定义（如有复杂参数）"""
    name: str
    description: str
    type: str
    required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "XxxParameter":
        return cls(**data)


@dataclass
class Xxx(Base):
    """工具实体 - 同时是 ORM 模型也是业务实体"""
    __tablename__ = "xxx"

    # 数据库字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
```

### 2. dtos.py - 数据传输对象层

```python
from typing import Optional, List
from pydantic import BaseModel, Field

class XxxDto(BaseModel):
    """API 响应 DTO"""
    id: int = Field(..., description="ID")
    name: str = Field(..., description="名称")
    # ... 其他字段

    class Config:
        json_schema_extra = {
            "example": {...}
        }

# 按需添加精简版 DTO
class XxxListDto(BaseModel):
    """列表响应 DTO"""
    data: List[XxxDto] = Field(default_factory=list)
```

### 3. dao.py - 数据访问层

```python
from typing import Optional, List
from injector import inject
from .models import Xxx
from ..datasource.connection import Connection

class XxxDao:
    """数据访问对象"""

    @inject
    def __init__(self, conn: Connection):
        self._conn = conn
        self.create_table()  # 可选：建表

    def get_by_id(self, id: int) -> Optional[Xxx]:
        ...

    def get_all(self) -> List[Xxx]:
        ...

    def create(self, xxx: Xxx) -> int:
        ...

    def update(self, xxx: Xxx) -> bool:
        ...

    def delete(self, id: int) -> bool:
        ...
```

### 4. service.py - 服务层

```python
from typing import List, Optional
from injector import inject
from .models import Xxx
from .dao import XxxDao
from .dtos import XxxDto
from src.modules.base import IService, ValidException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IXxxService(IService[XxxDto, int]):
    """服务接口

    继承 IService[ToolDto, int]，约束返回数据类型为 DTO，ID 类型为 int。
    """

    # 可扩展接口特有方法
    pass


class XxxService(IXxxService):
    """服务实现

    实现 IXxxService 接口，使用 @inject 装饰器进行依赖注入。
    """

    @inject
    def __init__(self, dao: XxxDao):
        self._dao = dao

    def get_list(self) -> List[XxxDto]:
        return [self.convert_dto(x) for x in self._dao.get_all()]

    def get_one(self, id: int) -> Optional[XxxDto]:
        xxx = self._dao.get_by_id(id)
        return self.convert_dto(xxx) if xxx else None

    def create_one(self, data: dict) -> XxxDto:
        # 校验逻辑
        if not data.get("name"):
            raise ValidException("名称不能为空", "name")

        # 业务逻辑
        xxx = Xxx(name=data["name"], description=data.get("description", ""))
        xxx_id = self._dao.create(xxx)
        xxx.id = xxx_id

        return self.convert_dto(xxx)

    def update(self, id: int, data: dict) -> Optional[Xxx]:
        xxx = self._dao.get_by_id(id)
        if not xxx:
            raise ValidException("记录不存在", "id")

        if "name" in data:
            xxx.name = data["name"]
        if "description" in data:
            xxx.description = data["description"]

        self._dao.update(xxx)
        return xxx

    def delete_by_id(self, id: int) -> bool:
        xxx = self._dao.get_by_id(id)
        if not xxx:
            raise ValidException("记录不存在", "id")
        self._dao.delete(id)
        return True

    def convert_dto(self, entity) -> XxxDto:
        if isinstance(entity, Xxx):
            data = entity.to_dict()
        else:
            data = entity
        return XxxDto(**data)
```

### 5. 注册依赖注入

模块通过 `InjectModuleInitializer` 自动注册，只需在 `src/modules/__init__.py` 中添加 Module 定义：

```python
from injector import Module, singleton, Binder

# 导入实体、Service、Dao
from .xxx import Xxx, XxxService, XxxDao


class XxxModule(Module):
    """Xxx 模块配置"""

    def configure(self, binder: Binder):
        # DAO - 单例
        binder.bind(
            XxxDao,
            scope=singleton
        )
        # Service - 单例
        binder.bind(
            XxxService,
            scope=singleton
        )


__all__ = [..., "Xxx", "XxxService", "XxxDao", "XxxModule"]
```

**获取服务**：在 API 层使用 `get_service()` 函数获取（无需手动获取 Injector）：

```python
from src.core import get_service
from src.modules import XxxService

_service = get_service(XxxService)
```

### 6. API 路由层

在 `src/api/xxx.py` 中：

```python
from fastapi import APIRouter, Query
from src.api.models import ApiResponse
from src.core import get_service
from src.modules import XxxService
from src.modules.base import ValidException
from src.utils.logger import get_logger
from .dtos import XxxDto

router = APIRouter(prefix="/api/xxx", tags=["xxx"])

# 使用 get_service 获取服务实例
_service = get_service(XxxService)
# 使用 get_logger 获取日志器
_logger = get_logger(__name__)


@router.get("")
async def get_xxx_list():
    """获取列表"""
    return ApiResponse.ok(_service.get_list())


@router.get("/{id}")
async def get_xxx(id: int):
    """获取单个"""
    dto = _service.get_one(id)
    if not dto:
        raise ValidException("记录不存在")
    return ApiResponse.ok(dto)


@router.post("")
async def create_xxx(request: dict):
    """创建"""
    dto = _service.create_one(request)
    _logger.info(f"[xxx_create] id={dto.id if dto else None}")
    return ApiResponse.ok(dto)


@router.put("/{id}")
async def update_xxx(id: int, request: dict = None):
    """更新"""
    dto = _service.update(id, request or {})
    if not dto:
        raise ValidException("记录不存在")
    _logger.info(f"[xxx_update] id={id}")
    return ApiResponse.ok(dto)


@router.delete("/{id}")
async def delete_xxx(id: int = Query(..., description="ID")):
    """删除"""
    success = _service.delete_by_id(id)
    return ApiResponse.ok(success)
```

### 7. 注册路由

在 `src/__main__.py` 中：

```python
from src.api import xxx_router

app.include_router(xxx_router)
```

### 关键要点速查

| 层级 | 文件 | 命名 | 类型 | 依赖注入 |
|------|------|------|------|----------|
| 实体 | models.py | Xxx | SQLAlchemy Base | - |
| DTO | dtos.py | XxxDto | Pydantic BaseModel | - |
| DAO | dao.py | XxxDao | class | @inject |
| Service | service.py | XxxService | class | @inject |
| API | api/xxx.py | - | FastAPI | get_service() |

**规范清单**：
- [ ] 实体继承 `Base`，使用 SQLAlchemy ORM
- [ ] DAO 使用 `@inject` 装饰器
- [ ] Service 使用 `@inject` 装饰器
- [ ] Service 继承 `IService[XxxDto, int]`
- [ ] Service 实现 `convert_dto()` 方法
- [ ] 校验失败抛出 `ValidException`
- [ ] API 返回 `ApiResponse.ok(data)`
- [ ] API 使用 `get_service()` 获取服务
- [ ] API 使用 `get_logger(__name__)` 获取日志器
- [ ] 在 `modules/__init__.py` 添加 Module 类

## 配置

主配置文件位于项目根目录 `config.yaml`：

```yaml
# LLM 提供商配置
llm:
  provider: qwen  # 可选: openai, qwen

# OpenAI API 配置（备选）
openai:
  api_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"

# Qwen API 配置
qwen:
  api_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "your-api-key"
  model: "qwen3-14b"
  enable_thinking: false  # 启用思考模式
  thinking_budget: 4000  # 思考预算

tools:
  allowed_tools: [bash, calculator, datetime, read_file, skill]
```

## 接口日志

### 功能特性

- **自动记录请求/响应**：所有 HTTP 请求自动记录（通过 `LoggingMiddleware`）
- **控制台简洁输出**：便于阅读
- **文件存储**：按时间轮转保存日志
- **敏感信息脱敏**：自动过滤密码、API 密钥等
- **日志轮转**：每天零点切割，保留 30 天

### 日志配置

日志系统在 Web 模式启动时自动初始化，通过 `ApplicationInitializer` 自动调用。

```python
from src.utils.logger import setup_logging, get_logger

# 初始化日志系统（在应用启动时调用一次）
setup_logging(
    log_dir="logs",           # 日志目录
    retention_days=30,       # 保留天数
)

# 在模块中获取日志器
logger = get_logger(__name__)
logger.info("message")
```

### 日志文件

- 目录：`backend/logs/`
- 文件：`api.log`
- 格式：标准 logging 格式（`%(asctime)s - %(name)s - %(levelname)s - %(message)s`）

### 使用示例

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info(f"[tool_create] id={tool_id}")
logger.error(f"[tool_execute_error] tool={tool_name}, error={str(e)}")
```

## 测试

当前仅有 `data/skills/pdf/scripts/check_bounding_boxes_test.py`，核心模块缺少单元测试。

## 代码质量

- **Python**: 3.9+，双引号字符串，Google 风格 docstring
- **black**: `line-length = 100`
- **isort**: `profile = black`

## 相关文件

| 文件 | 职责 |
|------|------|
| `src/__main__.py` | 应用入口 |
| `src/api/models.py` | 通用 API 响应模型（ApiResponse） |
| `src/api/tools.py` | 工具管理 API（参考模板） |
| `src/core/__init__.py` | 核心模块导出（get_service, get_app_config） |
| `src/modules/base.py` | 基础接口（IService, ValidException） |
| `src/modules/__init__.py` | 模块注册和注入器配置 |
| `src/modules/tools/models.py` | Tool 业务实体（ORM 模型参考） |
| `src/modules/tools/dtos.py` | Tool DTO |
| `src/modules/tools/dao.py` | Tool 数据访问 |
| `src/modules/tools/service.py` | Tool 服务层（参考模板） |
| `src/utils/logger.py` | 日志配置模块 |
| `src/web/logging_middleware.py` | HTTP 请求日志中间件 |
| `src/datasource/database.py` | SQLAlchemy 数据库基类 |
| `pyproject.toml` | 项目配置 |

**参考模板**：`src/modules/tools/` 目录下的 models.py → dtos.py → dao.py → service.py → api/tools.py

## 变更记录 (Changelog)

| 时间戳 | 操作 | 说明 |
|--------|------|------|
| 2026-02-03 11:32:16 | 初始化 | 首次生成 AI 上下文文档 |
| 2026-02-17 22:00:00 | 更新 | 更新为 WIMI CHAT 项目文档 |
| 2026-02-26 00:00:00 | 更新 | 完善模块文档，统一格式 |
| 2026-02-26 00:30:00 | 更新 | 更新接口日志、服务层、依赖注入、API路由层模板 |
