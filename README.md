# LLM CLI V3

LLM CLI V3 - 支持 Web 和 CLI 双模式的 AI 聊天应用。

## 特性

- **双模式支持**: CLI 交互模式和 Web 界面模式
- **流式响应**: 使用 SSE 实现实时流式输出
- **工具调用**: 支持 bash、calculator、datetime 等工具
- **技能系统**: 可扩展的技能模块
- **配置简单**: 通过 `config.yaml` 统一管理配置

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 配置

编辑 `config.yaml`：

```yaml
openai:
  api_base: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"
  temperature: 0.7

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

server:
  host: "0.0.0.0"
  port: 8000
```

### 3. 运行

#### Web 模式 (默认)

```bash
cd backend
python -m src

# 或显式指定
python -m src --web
```

访问 http://localhost:8000

#### CLI 模式

```bash
cd backend
python -m src --cli
```

### 4. 前端开发

```bash
cd frontend
npm run dev     # 开发模式
npm run build   # 构建生产版本
```

## 项目结构

```
llm-cli-v3/
├── backend/           # FastAPI 后端
│   ├── src/
│   │   ├── api/       # API 路由
│   │   ├── cli/       # CLI 交互层
│   │   ├── core/      # 核心业务逻辑
│   │   ├── tools/     # 工具系统
│   │   ├── skills/    # 技能系统
│   │   ├── adapters/  # API 适配器
│   │   ├── config/    # 配置管理
│   │   ├── web/       # Web 专用模块
│   │   └── utils/     # 工具函数
│   └── static/        # 前端构建产物
├── frontend/          # Vue.js 前端
│   └── src/
│       ├── api/       # API 调用
│       ├── components/# UI 组件
│       ├── stores/    # 状态管理
│       └── composables# 组合式函数
├── data/              # 数据目录
│   └── skills/        # 技能文件
└── config.yaml        # 配置文件
```

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/chat` | POST | 同步聊天 |
| `/api/chat/stream` | GET | SSE 流式聊天 |
| `/api/tools` | GET | 工具列表 |

## 技术栈

- **后端**: FastAPI + Uvicorn + SSE
- **前端**: Vue 3 + Vite + Pinia + TailwindCSS
- **LLM**: OpenAI 兼容 API

## 许可证

MIT
