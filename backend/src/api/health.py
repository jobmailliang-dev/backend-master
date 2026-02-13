"""健康检查 API 路由。"""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str
    version: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """检查服务健康状态。"""
    return HealthResponse(
        status="ok",
        version="3.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
