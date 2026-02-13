# FastAPI 接口日志方案规划文档

## 已明确的决策

- 日志框架选用 Python 标准库 `logging`（轻量、无需额外依赖）
- 日志格式采用 JSON 结构化日志（便于后续分析和处理）
- 日志文件位置：`backend/logs/` 目录
- 配置文件继续使用 YAML 格式，与现有配置风格保持一致
- **日志轮转策略**：按时间轮转（每天零点切割，保留 30 天）
- **敏感信息过滤**：仅核心敏感字段（password、api_key、secret、token、credential 等）
- **SSE 流式接口**：仅记录头部（连接建立和关闭），不记录流式内容

## 整体规划概述

### 项目目标

为 FastAPI 后端服务实现完整的接口日志方案，支持：
- 自动记录所有 HTTP 请求/响应的详细信息
- 控制台彩色输出，便于开发调试
- 文件持久化存储，支持日志轮转
- 可配置的日志级别和过滤规则
- 敏感信息自动脱敏

### 技术栈

- **日志框架**：Python 标准库 `logging`
- **日志格式**：JSON 结构化日志
- **日志轮转**：`logging.handlers.TimedRotatingFileHandler`（标准库，按时间）
- **配置管理**：YAML + Pydantic 模型
- **Python 版本**：>= 3.9

### 主要阶段

1. **阶段 1**：配置模型和日志基础模块设计
2. **阶段 2**：日志中间件实现
3. **阶段 3**：集成到 FastAPI 应用
4. **阶段 4**：配置文档和使用示例

### 详细任务分解

#### 阶段 1：配置模型和日志基础模块设计

- **任务 1.1**：设计日志配置数据模型
  - 目标：定义清晰的配置结构
  - 输入：`config/models.py` 现有配置
  - 输出：`config/models.py` 新增 `LoggingConfig` 数据类
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\config\models.py`
  - 预估工作量：0.5 天

- **任务 1.2**：创建日志配置加载器
  - 目标：支持从 YAML 加载日志配置
  - 输入：`config/loader.py` 现有加载逻辑
  - 输出：`config/loader.py` 新增日志配置解析
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\config\loader.py`
  - 预估工作量：0.5 天

- **任务 1.3**：实现日志配置模块
  - 目标：创建可配置的统一日志器，支持控制台和文件输出
  - 输入：LoggingConfig 配置
  - 输出：`src/utils/logging_config.py`
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\utils\logging_config.py`（新建）
  - 预估工作量：1 天

#### 阶段 2：日志中间件实现

- **任务 2.1**：设计 HTTP 请求/响应日志模型
  - 目标：定义日志数据结构
  - 输入：FastAPI Request/Response 对象
  - 输出：`src/middleware/logging.py` 新增数据类
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\middleware\logging.py`（新建）
  - 预估工作量：0.5 天

- **任务 2.2**：实现日志中间件核心逻辑
  - 目标：捕获请求/响应并记录日志
  - 输入：FastAPI ASGI 应用
  - 输出：完整的中间件类
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\middleware\logging.py`
  - 预估工作量：1.5 天

- **任务 2.3**：实现 JSON 格式化器和敏感信息脱敏
  - 目标：将日志记录为 JSON 格式，自动脱敏敏感字段
  - 输入：日志记录对象
  - 输出：JSON 格式的日志字符串
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\middleware\logging.py`
  - 预估工作量：0.5 天

#### 阶段 3：集成到 FastAPI 应用

- **任务 3.1**：修改应用入口注册中间件
  - 目标：在 FastAPI 应用中启用日志中间件
  - 输入：`__main__.py` 应用初始化
  - 输出：中间件正确注册
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\src\__main__.py`
  - 预估工作量：0.5 天

- **任务 3.2**：更新配置文件示例
  - 目标：添加日志配置说明
  - 输入：项目根目录 `config.yaml`
  - 输出：完整的日志配置示例
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\config.yaml`（如存在）
  - 预估工作量：0.5 天

- **任务 3.3**：添加单元测试
  - 目标：验证日志功能正确性
  - 输入：`tests/` 目录
  - 输出：`tests/test_logging.py` 测试文件
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\tests\test_logging.py`（新建）
  - 预估工作量：1 天

#### 阶段 4：配置文档和使用示例

- **任务 4.1**：更新 CLAUDE.md 文档
  - 目标：记录日志模块的使用方法
  - 输入：`backend/CLAUDE.md`
  - 输出：添加日志模块说明
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\CLAUDE.md`
  - 预估工作量：0.5 天

- **任务 4.2**：创建日志模块 README
  - 目标：提供详细的使用文档
  - 输入：`docs/` 目录（如存在）
  - 输出：`docs/logging.md`（新建）
  - 涉及文件：`D:\work\python_demo_test\llm-cli-demo-v4\llm-cli-v4\backend\docs\logging.md`（新建）
  - 预估工作量：0.5 天

## 接口日志字段设计

### 核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `timestamp` | string | ISO 8601 时间戳 |
| `level` | string | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `logger` | string | 日志器名称 |
| `message` | string | 日志消息 |
| `request_id` | string | 请求唯一标识 (UUID) |

### HTTP 请求字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `client_ip` | string | 客户端 IP 地址 |
| `method` | string | HTTP 方法 |
| `path` | string | 请求路径 |
| `path_params` | object | 路径参数 |
| `query_params` | object | 查询参数 |
| `headers` | object | 请求头（不含敏感信息） |
| `body_size` | integer | 请求体大小（字节） |
| `user_agent` | string | User-Agent 头 |

### HTTP 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `status_code` | integer | HTTP 状态码 |
| `response_size` | integer | 响应体大小（字节） |
| `duration_ms` | number | 请求耗时（毫秒） |

### SSE 流式接口额外字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `event_type` | string | 事件类型 (stream_start/stream_end) |
| `stream_id` | string | 流标识符 |

## 用户反馈区域

```
用户确认决策：
1. 日志轮转策略：按时间轮转（每天零点切割，保留 30 天）
2. 敏感信息过滤：仅核心敏感字段（密码、API密钥等）
3. SSE 流式接口：仅记录头部（连接建立和关闭）

确认时间：2026-02-09
```

## 实施进度

- [x] 阶段 1：配置模型和日志基础模块设计
- [x] 阶段 2：日志中间件实现
- [x] 阶段 3：集成到 FastAPI 应用
- [x] 阶段 4：配置文档和使用示例

### 完成的任务

1. **任务 1.1 & 1.2 & 1.3**：`src/utils/logging_config.py` - 日志配置模块
   - LoggingConfig 数据类
   - 敏感字段脱敏函数
   - JSON 格式化器
   - TimedRotatingFileHandler 时间轮转

2. **任务 2.1 & 2.2 & 2.3**：`src/web/logging_middleware.py` - 日志中间件
   - RequestLoggingMiddleware 中间件
   - SSEEventLogger 日志器
   - 客户端 IP 获取
   - 请求体/响应体日志

3. **任务 3.1**：更新 `src/__main__.py`
   - 集成日志中间件
   - 应用启动时初始化日志系统

4. **任务 3.2**：更新 `src/api/chat.py`
   - 集成 SSE 日志器
   - 记录流开始/结束事件

5. **任务 4.1**：更新 `CLAUDE.md`
   - 添加日志模块说明

6. **任务 4.2**：`docs/logging.md` - 详细使用文档
