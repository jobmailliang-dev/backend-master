"""HTTP 请求工具。

发送 HTTP 请求并返回响应结果。
"""

import httpx
from typing import Any, Dict, Optional

from src.tools.base import BaseTool


class HttpTool(BaseTool):
    """发送 HTTP 请求的工具。"""

    def __init__(self):
        """初始化 HTTP 工具。"""
        super().__init__(
            name="http",
            description="Send an HTTP request and return the response",
        )
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """获取或创建 HTTP 客户端。"""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                },
                "url": {
                    "type": "string",
                    "description": "The request URL",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers as key-value pairs (optional)",
                    "additionalProperties": {"type": "string"},
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters as key-value pairs (optional)",
                    "additionalProperties": {"type": "string"},
                },
                "json": {
                    "type": "object",
                    "description": "JSON body data (optional)",
                },
                "data": {
                    "type": "object",
                    "description": "Form data as key-value pairs (optional)",
                    "additionalProperties": {"type": "string"},
                },
                "content": {
                    "type": "string",
                    "description": "Raw request body content (optional)",
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow redirects (default: true)",
                    "default": True,
                },
            },
            "required": ["method", "url"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """发送 HTTP 请求。"""
        method = kwargs.get("method", "GET").upper()
        url = kwargs.get("url", "")
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})
        json_data = kwargs.get("json", None)
        form_data = kwargs.get("data", None)
        content = kwargs.get("content", None)
        follow_redirects = kwargs.get("follow_redirects", True)

        print(f"HTTP({method} {url})")

        if not url:
            raise ValueError("URL cannot be empty")

        client = self._get_client()

        try:
            response = client.request(
                method=method,
                url=url,
                headers=headers if headers else None,
                params=params if params else None,
                json=json_data,
                data=form_data if form_data else None,
                content=content,
                follow_redirects=follow_redirects,
            )

            # 尝试解析 JSON 响应
            try:
                response_json = response.json()
            except Exception:
                response_json = None

            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "method": method,
                "url": str(response.url),
                "headers": dict(response.headers),
                "content": response.text,
                "json": response_json,
            }

        except httpx.TimeoutException:
            raise ValueError(f"Request timed out: {url}")
        except httpx.ConnectError as e:
            raise ValueError(f"Connection failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Request failed: {str(e)}")

    def close(self):
        """关闭 HTTP 客户端。"""
        if self._client:
            self._client.close()
            self._client = None

    def __repr__(self) -> str:
        return f"HttpTool(name={self.name})"
