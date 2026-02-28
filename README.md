# LLM CLI V4

LLM CLI V4 - 支持 Web 和 CLI 双模式的 AI 聊天应用。

## 特性

- **双模式支持**: CLI 交互模式和 Web 界面模式
- **流式响应**: 使用 SSE 实现实时流式输出
- **工具调用**: 支持 bash、calculator、datetime 等工具
- **技能系统**: 可扩展的技能模块
- **配置简单**: 通过 `config.yaml` 统一管理配置

## 快速开始

### 1. 创建 Conda 环境

```bash
# 创建 Python 3.11 环境
conda create -n llm python=3.11.14

# 激活环境
conda activate llm
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置 API Key

复制环境变量示例文件并配置 API Key：

```bash
cp .env.example .env.dev
```

编辑 `.env.dev`，修改以下配置：

```bash
API_URL=your-api-url
API_KEY=your-api-key
API_MODEL=your-model
LOG_LEVEL=INFO
```

### 4. 运行

#### CLI 模式

```bash
python -m src --cli
```

#### Web 模式

```bash
python -m src
```

访问 http://localhost:8000

### 5. 配置 (可选)

如需修改更多配置信息，编辑 `config.yaml`：

```yaml
# 启用工具
tools:
  enabled: true
  show_tool_calls: true
  max_tool_calls: 5
  allowed_tools:
    - bash
    - calculator
    - datetime
    - read_file
    - skill
```

### 6. MCP 服务器配置 (可选)

支持通过 MCP (Model Context Protocol) 扩展工具。编辑 `mcp_servers.json`：

```json
{
  "fetch": {
    "command": "uvx",
    "args": ["mcp-server-fetch"]
  }
}
```

### 7. 技能系统 (可选)

技能是预定义的上下文内容，可在对话中动态加载。在 `data/skills` 目录下编写技能文件：

```
data/skills/
├── pdf/
│   └── SKILL.md       # PDF 处理技能
└── order/
    └── SKILL.md       # 订单管理技能
```

**技能文件格式** (`SKILL.md`)：

```yaml
---
name: pdf
description: PDF 处理技能，用于读取、创建、编辑 PDF 文档
---

# PDF 处理指南

## 常用操作

### 读取 PDF
...

### 提取表格
...
```

技能通过 `skill` 工具调用：

```
请使用 pdf 技能处理这个文档
```

## 项目结构

```
backend/
├── src/
│   ├── api/          # API 路由
│   ├── cli/          # CLI 交互层
│   ├── core/         # 核心业务逻辑
│   ├── tools/        # 工具系统
│   ├── skills/       # 技能系统
│   ├── adapters/     # API 适配器
│   ├── config/       # 配置管理
│   ├── web/          # Web 专用模块
│   └── utils/        # 工具函数
├── static/           # 前端构建产物
└── config.yaml       # 配置文件
```


## 技术栈

- **后端**: FastAPI + Uvicorn + SSE
- **LLM**: OpenAI 兼容 API

## 许可证

MIT
