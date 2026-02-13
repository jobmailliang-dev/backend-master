[根目录](../../CLAUDE.md) > [llm-cli-v3](../) > **backend**

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 模块职责

Backend 模块是 LLM CLI V3 的核心后端服务，提供：

- **Web 服务**: FastAPI 服务，支持 SSE 流式响应
- **LLM 客户端**: 集成 OpenAI 兼容 API，处理对话和工具调用
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
| `/chat` | POST | 同步聊天 |
| `/chat/stream` | GET | SSE 流式聊天 |
| `/health` | GET | 健康检查 |

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
│   └── logging_web.py    # 日志配置
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

```python
from dataclasses import dataclass
import sqlite3

@dataclass
class Xxx:
    """业务实体"""
    id: Optional[int] = None
    name: str = ""
    # ... 其他字段

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Xxx":
        """从数据库行创建实体"""
        ...

    def to_dict(self) -> dict:
        """转换为字典"""
        ...
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

# 接口定义
class IXxxService(IService[XxxDto], Protocol):
    """服务接口"""

    def get_list(self) -> List[XxxDto]:
        ...

    def get_one(self, id: int) -> Optional[XxxDto]:
        ...

    def create_one(self, data: dict) -> XxxDto:
        ...

    def update(self, id: int, data: dict) -> Optional[Xxx]:
        ...

    def delete_by_id(self, id: int) -> bool:
        ...

    def convert_dto(self, entity: Xxx) -> XxxDto:
        """实体转 DTO"""
        ...


# 实现类
class XxxService(IXxxService):
    """服务实现"""

    @inject
    def __init__(self, dao: XxxDao):
        self._dao = dao

    def get_list(self) -> List[XxxDto]:
        return [self.convert_dto(x) for x in self._dao.get_all()]

    def create_one(self, data: dict) -> XxxDto:
        # 校验逻辑
        if not data.get("name"):
            raise ValidException("名称不能为空", "name")
        # 业务逻辑
        ...
        return self.convert_dto(entity)

    def convert_dto(self, entity: Xxx) -> XxxDto:
        return XxxDto(**entity.to_dict())
```

### 5. 注册依赖注入

在 `src/modules/__init__.py` 中：

```python
from .xxx import Xxx, XxxService, XxxDao

class XxxModule(Module):
    def configure(self, binder: Binder):
        binder.bind(XxxDao, scope=singleton)
        binder.bind(XxxService, scope=singleton)

injector = Injector([
    DatabaseModule(),
    XxxModule(),  # 添加
])

__all__ = [..., "Xxx", "XxxService", "XxxDao"]
```

### 6. API 路由层

在 `src/api/xxx.py` 中：

```python
from fastapi import APIRouter, Query
from src.api.models import ApiResponse
from src.modules import XxxService, get_injector
from src.modules.base import ValidException
from .dtos import XxxDto

router = APIRouter(prefix="/api/xxx", tags=["xxx"])
_injector = get_injector()

@router.get("")
async def get_xxx_list():
    """获取列表"""
    service: XxxService = _injector.get(XxxService)
    return ApiResponse.ok(service.get_list())

@router.get("/{id}")
async def get_xxx(id: int):
    """获取单个"""
    service: XxxService = _injector.get(XxxService)
    dto = service.get_one(id)
    if not dto:
        raise ValidException("xxx not found")
    return ApiResponse.ok(dto)

@router.post("")
async def create_xxx(request: dict):
    """创建"""
    service: XxxService = _injector.get(XxxService)
    dto = service.create_one(request)
    return ApiResponse.ok(dto)

@router.put("/{id}")
async def update_xxx(id: int, request: dict):
    """更新"""
    service: XxxService = _injector.get(XxxService)
    dto = service.update(id, request)
    if not dto:
        raise ValidException("xxx not found")
    return ApiResponse.ok(dto)

@router.delete("/{id}")
async def delete_xxx(id: int):
    """删除"""
    service: XxxService = _injector.get(XxxService)
    success = service.delete_by_id(id)
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
| 实体 | models.py | Xxx | @dataclass | - |
| DTO | dtos.py | XxxDto | Pydantic BaseModel | - |
| DAO | dao.py | XxxDao | class | @inject(conn) |
| Service | service.py | XxxService | class | @inject(xxx_dao) |
| API | api/xxx.py | - | FastAPI | _injector.get() |

**规范清单**：
- [ ] DAO 使用 `@inject` 装饰器
- [ ] Service 使用 `@inject` 装饰器
- [ ] Service 继承 `IService[XxxDto]`
- [ ] Service 实现 `convert_dto()` 方法
- [ ] 校验失败抛出 `ValidException`
- [ ] API 返回 `ApiResponse.ok(data)`
- [ ] API 异常抛出 `ValidException`（中间件统一处理）
- [ ] 在 `modules/__init__.py` 注册模块

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

- **自动记录请求/响应**：所有 HTTP 请求自动记录
- **控制台简洁输出**：便于阅读
- **JSON 文件存储**：便于后续分析
- **敏感信息脱敏**：自动过滤密码、API 密钥等
- **日志轮转**：每天零点切割，保留 30 天

### 日志配置

日志系统在 Web 模式启动时自动初始化，无需手动配置。

```python
from src.utils.logging_web import setup_logging

# 自定义配置
logger = setup_logging(
    log_level="INFO",       # 日志级别
    console_output=True,    # 控制台输出
    file_output=True,       # 文件输出
    retention_days=30,     # 保留天数
)
```

### 日志文件

- 目录：`backend/logs/`
- 文件：`api.log`
- 格式：JSON 结构化日志

### 使用示例

```python
from src.utils.logging_web import get_request_logger

logger = get_request_logger("src.api.tools")
logger.info(f"[tool_create] id={tool_id}, body={body_str}")
```

详细文档：[docs/logging.md](../docs/logging.md)

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
| `src/api/tools.py` | 工具管理 API |
| `src/modules/base.py` | 基础接口（IService, ValidException） |
| `src/modules/tools/models.py` | Tool 业务实体 |
| `src/modules/tools/dtos.py` | Tool DTO |
| `src/modules/tools/dao.py` | Tool 数据访问 |
| `src/modules/tools/service.py` | Tool 服务层 |
| `src/utils/logging_web.py` | 日志配置模块 |
| `src/web/logging_middleware.py` | HTTP 请求日志中间件 |
| `docs/logging.md` | 日志模块文档 |
| `pyproject.toml` | 项目配置 |

**参考模板**：`src/modules/tools/` 目录下的 models.py → dtos.py → dao.py → service.py → api/tools.py
