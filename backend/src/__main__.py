"""LLM CLI V3 - 应用入口。"""

import argparse
import logging
import sys
from pathlib import Path

# 禁用 Uvicorn 默认访问日志，保留自定义中间件的简洁输出
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.WARNING)

# 添加 src 目录到 Python 路径
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent.parent


def setup_python_path():
    """设置 Python 路径。"""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def run_cli():
    """运行 CLI 模式。"""
    from src.cli.interface import run_cli as cli_main
    cli_main()


def run_web():
    """运行 Web 模式。"""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from src.api import chat_router, health_router, test_router, tools_router
    from src.api.conversations import router as conversations_router
    from src.utils.logging_web import setup_logging
    from src.web.cors import setup_cors
    from src.web.logging_middleware import RequestLoggingMiddleware

    # 初始化日志系统
    logger = setup_logging(
        log_level="INFO",
        console_output=True,
        file_output=True,
        retention_days=30,
    )

    app = FastAPI(
        title="LLM CLI V3",
        description="A web interface for LLM CLI with streaming support",
        version="3.0.0",
    )

    # 添加请求日志中间件（最后注册，确保最先执行）
    app.add_middleware(RequestLoggingMiddleware)

    # 配置 CORS
    setup_cors(app)

    # 注册路由 (tools 最先注册，显示在 API 文档最上方)
    app.include_router(tools_router)
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(test_router)
    app.include_router(conversations_router)

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

    # 获取端口配置
    config_file = PROJECT_ROOT / "config.yaml"
    port = 8000
    host = "0.0.0.0"

    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                port = config.get('server', {}).get('port', 8000)
                host = config.get('server', {}).get('host', '0.0.0.0')
        except Exception:
            pass

    print(f"Starting LLM CLI V3 Web Server...")
    print(f"http://{host}:{port}")
    print(f"API Docs: http://{host}:{port}/docs")
    logger.info(f"Server started on http://{host}:{port}")

    uvicorn.run(app, host=host, port=port)


def main():
    """主入口函数。"""
    parser = argparse.ArgumentParser(
        description="LLM CLI V3 - 支持 CLI 和 Web 模式"
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "web"],
        default="web",
        help="运行模式: cli 或 web (默认: web)"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="以 CLI 模式运行（等价于 --mode cli）"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="以 Web 模式运行（等价于 --mode web）"
    )

    args = parser.parse_args()

    from src.tools import registry_init  # noqa: F401
    from src.cli.interface import run_cli

    # 确定运行模式
    if args.cli:
        mode = "cli"
    elif args.web:
        mode = "web"
    else:
        mode = args.mode

    # 设置 Python 路径
    setup_python_path()

    # 运行对应模式
    if mode == "cli":
        run_cli()
    else:
        run_web()


if __name__ == "__main__":
    main()
