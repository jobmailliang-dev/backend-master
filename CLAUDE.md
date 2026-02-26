# WIMI CHAT - 后端模块

[根目录](../CLAUDE.md) > **backend-master**

## 项目愿景

WIMI CHAT 后端模块 - 基于 FastAPI 的 AI 聊天后端服务。支持 Web 和 CLI 双模式，提供 SSE 流式响应、工具调用、技能系统。

## 模块索引

| 子模块 | 路径 | 职责 |
|--------|------|------|
| **backend** | `backend/` | FastAPI 后端核心服务 |
| **data/skills** | `data/skills/` | 技能数据目录 |

## 快速开始

### 后端服务

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# Web 模式（默认端口 8000）
python -m src --web

# CLI 模式
python -m src --cli

# 指定端口
python -m src --port 8080
```

### 前后端联调

```bash
# 终端 1: 启动后端
cd backend && python -m src --web

# 终端 2: 启动前端
cd ../frontend-master/frontend_chat && pnpm dev
```

## 架构概览

```
backend-master/
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── api/          # API 路由层
│   │   ├── core/         # 核心业务逻辑
│   │   ├── tools/        # 工具系统
│   │   ├── skills/       # 技能系统
│   │   ├── modules/      # 业务模块（依赖注入）
│   │   ├── adapters/     # LLM 适配器
│   │   ├── config/       # 配置管理
│   │   └── __main__.py   # 应用入口
│   └── config.yaml       # 配置文件
├── data/                 # 技能数据
│   └── skills/           # 技能目录
└── config.yaml           # 配置文件（链接到 backend）
```

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI 0.109+ |
| ASGI 服务器 | Uvicorn |
| 依赖注入 | injector |
| 数据库 | SQLite |
| LLM 提供商 | OpenAI / Qwen (通义千问) |

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/chat` | POST | 同步聊天 |
| `/api/chat/stream` | GET | SSE 流式聊天 |
| `/api/tools` | GET | 工具列表 |
| `/docs` | - | Swagger API 文档 |

## 配置文件

所有配置通过 `config.yaml` 管理：

```yaml
llm:
  provider: qwen  # 可选: openai, qwen

openai:
  api_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"

qwen:
  api_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "your-api-key"
  model: "qwen3-14b"
  enable_thinking: false

tools:
  allowed_tools:
    - bash
    - calculator
    - datetime
    - read_file
    - skill

server:
  host: "0.0.0.0"
  port: 8000
```

## 详细文档

- [backend/CLAUDE.md](backend/CLAUDE.md) - 后端核心模块详细文档
- [data/skills/CLAUDE.md](data/skills/CLAUDE.md) - 技能系统详细文档

## 变更记录 (Changelog)

| 时间戳 | 操作 | 说明 |
|--------|------|------|
| 2026-02-17 22:00:00 | 更新 | 更新为 WIMI CHAT 项目文档 |
| 2026-02-26 00:00:00 | 更新 | 完善模块索引和技术栈说明 |
