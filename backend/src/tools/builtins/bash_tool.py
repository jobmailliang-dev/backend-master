"""Bash 工具。

在当前 shell 环境中执行命令并返回结果。
"""

import platform
import subprocess
from typing import Any, Dict

from src.tools.base import BaseTool


class BashTool(BaseTool):
    """在当前 shell 环境中执行命令的工具。"""

    def __init__(self):
        """初始化 Bash 工具。"""
        super().__init__(
            name="bash",
            description="Execute a bash command in the current shell environment and return the result",
        )
        # 检测 Windows 环境，使用 GBK 编码；其他环境使用 UTF-8
        self._encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what this command does (optional)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60,
                },
            },
            "required": ["command"],
        }

    def _decode_output(self, data: bytes) -> str:
        """解码输出，Windows 上优先 GBK，失败则尝试 UTF-8。"""
        if not data:
            return ""
        # 优先使用首选编码
        try:
            return data.decode(self._encoding)
        except UnicodeDecodeError:
            # 备用 UTF-8 编码
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                # 最后使用 ignore 策略
                return data.decode("utf-8", errors="ignore")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 bash 命令。"""
        command = kwargs.get('command', '')
        timeout = kwargs.get('timeout', 60)

        print(f"Bash({command})")

        if not command:
            raise ValueError("Command cannot be empty")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=False,  # 获取二进制，手动解码
                timeout=timeout,
            )

            return {
                "success": result.returncode == 0,
                "command": command,
                "stdout": self._decode_output(result.stdout),
                "stderr": self._decode_output(result.stderr),
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            raise ValueError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise ValueError(f"Failed to execute command: {str(e)}")

    def __repr__(self) -> str:
        return f"BashTool(name={self.name})"
