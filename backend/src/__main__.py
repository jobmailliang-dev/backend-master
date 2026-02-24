"""LLM CLI V4 - 应用入口。"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from src.core import ApplicationInitializer, get_app_config

# 添加 src 目录到 Python 路径
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent.parent

def run_web(env: str = "dev"):
    """运行 Web 模式。

    Args:
        env: 环境名称 (dev, prod, local)
    """
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from src.api import chat_router, health_router, test_router, tools_router
    from src.api.conversations import router as conversations_router
    from src.web.cors import setup_cors
    from src.web.logging_middleware import RequestLoggingMiddleware
    from src.utils.logger import get_logger
    logger = get_logger(__name__)

    app = FastAPI(
        title="WIMI LLM WEB V4",
        description="A web interface for LLM CLI with streaming support",
        version="4.0.0",
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
    # 支持两种路径：本地开发 (backend/static) 和 Docker 部署 (/app/static)
    static_dir = os.environ.get('STATIC_DIR', PROJECT_ROOT / "backend" / "static")
    if isinstance(static_dir, str):
        static_dir = Path(static_dir)
    if static_dir.exists():
        # 挂载到根路径，直接映射 assets
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
        app.mount("/favicon.ico", StaticFiles(directory=str(static_dir)), name="favicon")

        # 根路径返回 index.html
        @app.get("/")
        async def root():
            from fastapi.responses import FileResponse
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"status": "ok", "message": "LLM CLI V4 API", "docs": "/docs"}

    # 获取端口配置（从已加载的配置中获取，或使用默认值）
    app_config = get_app_config()
    if app_config.server:
        port = int(app_config.server.port)
        host = app_config.server.host
    else:
        port = 8000
        host = "0.0.0.0"

    print(f"Starting LLM CLI V4 Web Server...")
    print(f"http://{host}:{port}")
    print(f"API Docs: http://{host}:{port}/docs")
    logger.info(f"Server started on http://{host}:{port}")

    uvicorn.run(app, host=host, port=port)


def main():
    """主入口函数。"""
    # 使用新的初始化模块
    ApplicationInitializer.initialize()

    parser = argparse.ArgumentParser(
        description="LLM CLI V4 - 支持 CLI 和 Web 模式"
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
    parser.add_argument(
        "--env",
        choices=["dev", "prod", "local"],
        default=None,
        help="运行环境: dev, prod, local (默认: dev 或 APP_ENV 环境变量)"
    )

    args = parser.parse_args()
    

    # 确定运行模式
    if args.cli:
        mode = "cli"
    elif args.web:
        mode = "web"
    else:
        mode = args.mode

    # 运行对应模式
    if mode == "cli":
        from src.tools import registry_init  # noqa: F401
        from src.cli.interface import run_cli
        run_cli()
    else:
        run_web(env=args.env)


if __name__ == "__main__": 
    main()