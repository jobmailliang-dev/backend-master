# CLAUDE.md

本文档为 Claude Code 提供 llm-cli-v3 项目的上下文和开发指导。

## 项目愿景

**LLM CLI V3** - 支持 Web 和 CLI 双模式的 AI 聊天应用。基于 llm-cli-v2 重构，添加 FastAPI 后端和 Vue.js 前端，支持 SSE 流式响应。

## 架构总览

```
llm-cli-v3/
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── api/          # API 路由层
│   │   │   ├── chat.py   # 聊天接口 (REST + SSE)
│   │   │   └── health.py # 健康检查
│   │   ├── web/          # Web 专用模块
│   │   │   ├── sse.py    # SSE 流式处理
│   │   │   └── cors.py   # CORS 配置
│   │   ├── cli/          # CLI 交互层 (复用 v2)
│   │   ├── core/         # 核心业务逻辑 (复用 v2)
│   │   ├── tools/        # 工具系统 (复用 v2)
│   │   ├── skills/       # 技能系统 (复用 v2)
│   │   ├── adapters/     # API 适配器 (复用 v2)
│   │   ├── config/       # 配置管理 (复用 v2)
│   │   ├── utils/        # 通用工具 (复用 v2)
│   │   └── __main__.py   # 应用入口 (CLI/Web 双模式)
│   ├── static/           # 前端构建产物
│   └── requirements.txt  # 依赖
├── frontend/             # Vue.js 前端
│   ├── src/
│   │   ├── api/          # API 调用封装
│   │   ├── components/   # UI 组件
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── composables/  # 组合式函数
│   │   ├── types/        # 类型定义
│   │   ├── assets/       # 静态资源
│   │   ├── App.vue       # 根组件
│   │   └── main.ts       # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/                 # 技能数据 (复用 v2)
└── config.yaml           # 配置文件
```

## 运行与开发

### 后端 (Web 模式)

```bash
cd backend
pip install -r requirements.txt
python -m src              # 默认 Web 模式 (端口 8000)
python -m src --web        # 显式 Web 模式
python -m src --cli        # CLI 模式
python -m src --port 8080  # 指定端口
```

### 前端 (开发模式)

```bash
cd frontend
npm install
npm run dev                # 开发服务器 (端口 3000)
npm run build             # 构建生产版本
```

### 前后端联调

```bash
# 终端 1: 启动后端
cd backend && python -m src --web

# 终端 2: 启动前端开发服务器
cd frontend && npm run dev
```

访问 http://localhost:3000 (开发) 或 http://localhost:8000 (生产构建)

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/chat` | POST | 同步聊天 |
| `/api/chat/stream` | GET | SSE 流式聊天 |
| `/api/tools` | GET | 工具列表 |
| `/docs` | - | Swagger API 文档 |

### SSE 事件协议

| 事件名 | 数据格式 | 说明 |
|--------|----------|------|
| `content` | string | 文本内容块 |
| `tool_call` | JSON | 工具调用信息 |
| `done` | 空 | 流结束信号 |
| `error` | JSON | 错误信息 |

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI 0.109+ |
| ASGI 服务器 | Uvicorn |
| 前端框架 | Vue 3 + TypeScript |
| 构建工具 | Vite 5.x |
| 状态管理 | Pinia |
| HTTP 客户端 | Axios |
| 样式框架 | TailwindCSS |

## 编码规范

### Python 规范

- **Python 版本**：3.9 及以上
- **类型提示**：必须使用类型注解
- **代码风格**：PEP 8 风格指南，双引号字符串
- **函数长度**：建议控制在 50 行以内
- **文档字符串**：Google 风格

### TypeScript 规范

- **Vue 3**：使用 Composition API + `<script setup>`
- **类型安全**：严格模式启用
- **组件命名**：PascalCase (如 `ChatWindow.vue`)
- **导入排序**：Vue API → 第三方 → 本地导入

### Dialog 组件规范

Dialog/Modal 弹窗组件统一使用以下样式规范：

#### 1. 模板结构
```vue
<Teleport to="body">
  <Transition name="dialog">
    <div v-if="visible" class="dialog-overlay" @click="handleCancel">
      <div class="dialog-container" @click.stop>
        <!-- 标题栏 -->
        <div class="dialog-header">
          <h3 class="dialog-title">{{ title }}</h3>
          <button class="close-btn" @click="handleCancel">×</button>
        </div>
        <!-- 内容区/输入框 -->
        <div class="dialog-content">...</div>
        <!-- 操作栏 -->
        <div class="dialog-actions">...</div>
      </div>
    </div>
  </Transition>
</Teleport>
```

#### 2. 样式变量 (浅色主题)
```css
.dialog-overlay {
  --background-white: #ffffff;
  --text-primary: #1f1f1f;
  --text-secondary: rgba(0, 0, 0, 0.7);
  --text-tertiary: #8c8c8c;
  --fill-gray-light: #f5f5f5;
  --fill-gray-hover: #e8e8e8;
  --border-light: #e5e5e5;
  --icon-tertiary: #8c8c8c;
  --Button-primary-blue: #007aff;
  --Button-primary-red: #ff4d4f;
}
```

#### 3. 关键样式规格
| 属性 | 值 | 说明 |
|------|-----|------|
| 容器宽度 | 360-400px | 标准宽度 |
| 圆角 | 20px | 大圆角 |
| 阴影 | 0 24px 48px rgba(0,0,0,0.15) | 柔和阴影 |
| 遮罩 | rgba(0,0,0,0.4) + blur(4px) | 半透明磨砂 |
| 按钮高度 | 36px | 固定高度 |
| 按钮圆角 | 8px | 小圆角 |
| 过渡动画 | cubic-bezier(0.34,1.56,0.64,1) | 弹性效果 |

#### 4. 按钮类型
- **确认/主要按钮**：蓝色背景 + 白色文字
- **取消/次要按钮**：透明背景 + 边框
- **删除/危险按钮**：红色背景 + 白色文字

#### 5. 组件文件
- `ConfirmDialog.vue` - 确认对话框
- `RenameDialog.vue` - 重命名对话框

### 模块导出规范

后端模块的公共接口应在 `src/*/__init__.py` 中导出。

## 配置文件

所有配置通过 `config.yaml` 管理，前端无配置界面：

```yaml
openai:
  api_base: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"

tools:
  enabled: true
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

## 开发提示

### 添加新工具

复用 `src/tools/builtins/` 目录中的模式，无需修改 API 层。

### 添加新 API 端点

在 `src/api/` 目录添加新路由文件，并在 `__main__.py` 中注册。

### 前端组件开发

- 通用组件放在 `src/components/`
- 业务组件放在 `src/views/` (如需)
- 组合式函数放在 `src/composables/`
- 状态管理在 `src/stores/`

## 注意事项

1. **配置管理**：所有配置通过 `config.yaml`，前端不维护配置状态
2. **代码复用**：尽量复用 v2 的核心逻辑，减少重复代码
3. **SSE 流式**：使用 `EventSource` API 处理流式响应
4. **跨域配置**：开发环境 Vite 代理，生产环境 CORS 中间件
