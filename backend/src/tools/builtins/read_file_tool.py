"""文件读取工具。

读取本地文件内容。
"""

from pathlib import Path
from typing import Any, Dict

from src.tools.base import BaseTool


class ReadFileTool(BaseTool):
    """读取本地文件的工具。"""

    def __init__(self):
        """初始化文件读取工具。"""
        super().__init__(
            name="read_file",
            description=(
                "Read the contents of a local file. "
                "Provide the file path relative to the project root. "
                "Returns the file content, line count, and metadata."
            ),
        )

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to project root, e.g., 'config.yaml' or 'src/main.py')",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (0 for all lines, default: 0)",
                    "default": 0,
                },
            },
            "required": ["file_path"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具，读取文件。"""
        file_path = kwargs.get('file_path')

        if not file_path:
            raise ValueError("file_path parameter is required")

        # 防止路径遍历攻击
        if '..' in file_path or file_path.startswith('/'):
            raise ValueError(f"Invalid file path: {file_path}")

        encoding = kwargs.get('encoding', 'utf-8')
        max_lines = kwargs.get('max_lines', 0)

        # 解析项目根目录
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path

        try:
            if not full_path.exists():
                raise ValueError(f"File not found: {file_path}")

            if not full_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")

            with open(full_path, 'r', encoding=encoding) as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip('\n\r'))
                    content = '\n'.join(lines)
                else:
                    content = f.read()

            stat = full_path.stat()
            line_count = content.count('\n') + (1 if content and not content.endswith('\n') else 0)

            return {
                "file_path": file_path,
                "content": content,
                "encoding": encoding,
                "line_count": line_count,
                "size_bytes": stat.st_size,
                "success": True,
            }

        except UnicodeDecodeError:
            raise ValueError(f"File cannot be decoded with encoding '{encoding}'. Try specifying a different encoding.")
        except PermissionError:
            raise ValueError(f"Permission denied to read file: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

    def __repr__(self) -> str:
        return f"ReadFileTool(name={self.name})"
