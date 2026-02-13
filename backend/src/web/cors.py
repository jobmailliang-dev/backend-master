"""CORS 配置模块。"""

from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    """配置 CORS 中间件。"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制为具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
