"""HTTP 请求日志中间件。

为 FastAPI 应用提供结构化的 HTTP 请求日志记录功能。
"""

import json
import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logging_web import API_LOGGER_NAME, get_request_logger
from src.modules.base import ApiException, ValidException


# 业务错误码
class BusinessCode:
    """业务错误码定义"""
    VALIDATION_ERROR = 2001  # 参数校验错误


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 请求日志中间件。

    自动记录所有 HTTP 请求的详细信息。
    """

    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = API_LOGGER_NAME,
    ) -> None:
        """初始化中间件。

        Args:
            app: ASGI 应用
            logger_name: 日志器名称
        """
        super().__init__(app)
        self.logger = get_request_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志。

        Args:
            request: FastAPI 请求对象
            call_next: 下一个处理器

        Returns:
            FastAPI 响应对象
        """
        # 生成请求 ID
        request_id = str(uuid.uuid4())

        # 记录请求开始时间
        start_time = time.perf_counter()

        # 获取客户端信息
        client_ip = self._get_client_ip(request)

        # 处理请求
        try:
            response = await call_next(request)

            # 计算耗时
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 记录响应日志（根据状态码选择级别）
            level = "ERROR" if response.status_code >= 400 else "INFO"
            log_msg = f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms) [{client_ip}]"
            if level == "ERROR":
                self.logger.error(log_msg)
            else:
                self.logger.info(log_msg)

            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id

            return response

        except ValidationError as exc:
            # 参数校验错误
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"{request.method} {request.url.path} VALIDATION_ERROR: {str(exc)} ({duration_ms:.2f}ms)"
            )
            # 返回包含错误码的响应
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": str(exc),
                    "error_code": BusinessCode.VALIDATION_ERROR,
                    "data": None
                },
                headers={"X-Request-ID": request_id}
            )

        except ApiException as exc:
            # API 业务异常
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"{request.method} {request.url.path} API_ERROR: {str(exc)} ({duration_ms:.2f}ms)"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": str(exc),
                    "data": None
                },
                headers={"X-Request-ID": request_id}
            )

        except ValidException as exc:
            # 参数校验异常
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"{request.method} {request.url.path} VALID_ERROR: {str(exc)} ({duration_ms:.2f}ms)"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": exc.message,
                    "error_code": BusinessCode.VALIDATION_ERROR,
                    "data": None
                },
                headers={"X-Request-ID": request_id}
            )

        except Exception as exc:
            # 记录其他异常
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                f"{request.method} {request.url.path} ERROR: {str(exc)} ({duration_ms:.2f}ms)"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP。"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        if request.client:
            return request.client.host
        return "unknown"
