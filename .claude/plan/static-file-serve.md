# 静态文件夹服务实施规划

## 1. 目标定义

### 1.1 核心目标

将前端 Vue3 打包后的 `dist` 目录整合到后端静态文件服务中，实现前后端一体化部署和运行，用户只需启动后端服务即可同时访问前端页面和 API 接口。

### 1.2 具体指标

| 指标 | 目标值 |
|------|--------|
| 前端页面访问 | 访问 `http://localhost:8000/` 返回 Vue3 应用 |
| 静态资源加载 | 所有 JS/CSS/字体等资源正常加载 |
| API 接口可用 | `/api/*` 接口正常工作 |
| SPA 路由支持 | 前端路由（刷新后）正常渲染 |

---

## 2. 功能分解

### 2.1 静态文件目录创建

- **F1.1**: 创建后端 `static` 目录（`backend/backend/static/`）
- **F1.2**: 确定前端资源同步方式（软链接/复制）
- **F1.3**: 验证目录结构和文件完整性

### 2.2 静态文件服务配置

- **F2.1**: 确认现有静态文件服务代码正常工作
- **F2.2**: 配置根路径 `/` 返回 `index.html`
- **F2.3**: 配置 `/static` 路径访问静态资源

### 2.3 SPA 路由支持（可选增强）

- **F3.1**: 配置 HTML5 History API 路由 fallback
- **F3.2**: 处理 404 情况返回 index.html

### 2.4 配置灵活性增强（可选）

- **F4.1**: 在 `config.yaml` 中添加静态文件配置项
- **F4.2**: 支持配置前端 dist 路径

---

## 3. 实施步骤

### 步骤 1: 创建 static 目录并同步前端资源

```bash
# 方案 A: 使用符号链接（推荐开发环境）
# 在 Windows 上需要管理员权限或启用开发者模式
mklink /D D:\work\python_demo_test\llm-cli-demo-v4\backend-master\backend\static D:\work\python_demo_test\llm-cli-demo-v4\frontend-master\frontend_chat\dist

# 方案 B: 使用复制（推荐生产环境）
# xcopy /E /I /Y D:\work\python_demo_test\llm-cli-demo-v4\frontend-master\frontend_chat\dist D:\work\python_demo_test\llm-cli-demo-v4\backend-master\backend\static
```

**推荐**：使用复制方式（方案 B），原因如下：
- 无需管理员权限
- 部署时更稳定，不依赖源目录
- 版本管理更清晰

### 步骤 2: 验证静态文件服务代码

检查 `D:\work\python_demo_test\llm-cli-demo-v4\backend-master\backend\src\__main__.py` 第 67-80 行，确认以下逻辑：

```python
# 静态文件服务（前端构建产物）
static_dir = PROJECT_ROOT / "backend" / "static"
if static_dir.exists():
    # 挂载到 /static 路径
    app.mount("/static", StaticFiles(directory=str(static_dir)))

    # 根路径返回 index.html
    @app.get("/")
    async def root():
        from fastapi.responses import FileResponse
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"status": "ok", "message": "LLM CLI V3 API", "docs": "/docs"}
```

该代码已存在且逻辑正确，无需修改。

### 步骤 3: 启动后端服务并验证

```bash
\python_demo_testcd D:\work\llm-cli-demo-v4\backend-master\backend
python -m src --web
```

### 步骤 4: 验证功能

| 验证项 | 预期结果 |
|--------|----------|
| 访问 `http://localhost:8000/` | 返回 index.html，页面正常渲染 |
| 访问 `http://localhost:8000/assets/*.js` | 返回对应的 JS 文件 |
| 访问 `http://localhost:8000/assets/*.css` | 返回对应的 CSS 文件 |
| 点击前端路由后刷新 | 页面正常显示（无 404） |
| 访问 `/api/health` | 返回健康检查响应 |

### 步骤 5: （可选）增强 SPA 路由支持

如果前端刷新出现 404，需要添加 fallback 处理。在 `__main__.py` 中添加：

```python
# SPA 路由支持 - 所有未匹配路由返回 index.html
@app.get("/{path:path}")
async def spa_fallback(path: str):
    from fastapi.responses import FileResponse
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "error", "message": "Not found"}
```

**注意**：此 fallback 需要放在所有 API 路由之后，避免拦截 API 请求。

### 步骤 6: （可选）配置灵活性增强

在 `config.yaml` 中添加静态文件配置：

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  static_dir: "backend/static"  # 静态文件目录，相对于项目根目录
  enable_spa_fallback: true    # 启用 SPA fallback
```

然后修改 `__main__.py` 读取配置：

```python静态文件配置

# 读取static_dir_name = config.get('server', {}).get('static_dir', 'backend/static')
static_dir = PROJECT_ROOT / static_dir_name
enable_spa = config.get('server', {}).get('enable_spa_fallback', False)
```

---

## 4. 验收标准

### 4.1 功能验收

| 编号 | 验收项 | 检查方法 |
|------|--------|----------|
| AC1 | 后端服务启动无报错 | 启动命令 `python -m src --web` 无异常 |
| AC2 | 访问根路径返回前端页面 | 浏览器访问 `http://localhost:8000/` |
| AC3 | JS 资源正常加载 | 浏览器 Network 面板无 404 |
| AC4 | CSS 资源正常加载 | 浏览器 Network 面板无 404 |
| AC5 | API 接口正常响应 | 访问 `/api/health` 返回 JSON |
| AC6 | 前端页面可交互 | 页面按钮、输入框等功能正常 |

### 4.2 视觉检查点

- 页面标题显示 "AI 助手"
- 聊天界面正常渲染
- 无控制台错误（Error 级别）

### 4.3 兼容性检查

| 环境 | 检查项 |
|------|--------|
| Windows | 目录路径处理正常 |
| 开发模式 | 每次修改前端后需重新同步 |
| 生产模式 | 一次性部署，长期运行 |

---

## 5. 技术方案对比

### 5.1 软链接 vs 复制

| 特性 | 软链接 | 复制 |
|------|--------|------|
| 磁盘空间 | 节省（仅一个目录） | 占用双份空间 |
| 同步方式 | 自动同步 | 需手动或脚本同步 |
| 权限要求 | 需管理员/开发者模式 | 无特殊要求 |
| 跨平台 | Unix/Linux 通用 | 完全跨平台 |
| 推荐场景 | 开发环境 | 生产环境 |

### 5.2 资源路径分析

前端 `index.html` 使用绝对路径：
```html
<script type="module" crossorigin src="/assets/index-1ab81544.js"></script>
<link rel="stylesheet" href="/assets/index-b64caaf6.css">
```

后端配置：
- `/` -> `static/index.html`
- `/assets/*` -> `static/assets/*`

路径匹配正确，无需修改前端构建配置。

---

## 6. 实施检查清单

- [ ] 创建 `backend/backend/static` 目录
- [ ] 复制前端 dist 目录内容到 static 目录
- [ ] 启动后端服务验证
- [ ] 验证前端页面正常访问
- [ ] 验证 API 接口正常
- [ ] （可选）添加 SPA fallback 支持
- [ ] （可选）添加配置文件支持

---

### Critical Files for Implementation

- `D:\work\python_demo_test\llm-cli-demo-v4\backend-master\backend\src\__main__.py` - 静态文件服务配置代码（第 67-80 行），主要修改位置
- `D:\work\python_demo_test\llm-cli-demo-v4\backend-master\config.yaml` - 服务器配置文件，可选添加静态文件配置项
- `D:\work\python_demo_test\llm-cli-demo-v4\frontend-master\frontend_chat\dist\index.html` - 前端入口文件，用于验证资源路径
- `D:\work\python_demo_test\llm-cli-demo-v4\backend-master\backend\CLAUDE.md` - 后端模块文档，包含运行命令和配置说明
- `D:\work\python_demo_test\llm-cli-demo-v4\frontend-master\frontend_chat\vite.config.ts` - 前端构建配置，如需调整资源路径可修改此文件
