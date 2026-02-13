"""QuickJS 工具。

执行 JavaScript 代码并返回结果。
"""

import asyncio
import json as pyjson
from typing import Any, Dict, List

import quickjs

from src.tools.base import BaseTool
from src.tools.quickjs.func_console import apply as apply_console
from src.tools.quickjs.call_tool import apply as apply_call_tool


class QuickJSTool(BaseTool):
    """JavaScript 执行工具。"""

    def __init__(self):
        """初始化 QuickJS 工具。"""
        super().__init__(
            name="quickjs",
            description="Execute JavaScript code and return the result",
        )
        self._context: quickjs.Context | None = None
        self._console_output: List[str] = []

    def _get_context(self) -> quickjs.Context:
        """获取或创建 JS 上下文。"""
        if self._context is None:
            self._context = quickjs.Context()
        return self._context

    def _register_console_functions(self) -> None:
        """注册 console 和工具调用函数。"""
        ctx = self._get_context()
        apply_console(ctx, self._console_output, tool_name=self.name)
        apply_call_tool(ctx)

    def _get_js_type(self, value: Any) -> str:
        """获取 JavaScript 结果类型。"""
        # quickjs.Object 类型需要通过 class_id 判断
        if isinstance(value, quickjs.Object):
            # 尝试转换为 Python 对象
            try:
                py_value = value.json
                if callable(py_value):
                    py_value = py_value()
                if isinstance(py_value, list):
                    return "array"
                if isinstance(py_value, dict):
                    return "object"
            except Exception:
                pass
            # 通过 JS 的 instanceof 判断
            try:
                ctx = self._get_context()
                is_array = ctx.eval(f"{value.js_id} instanceof Array")
                if is_array:
                    return "array"
            except Exception:
                pass
            return "object"

        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif value is None:
            return "null"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return type(value).__name__

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "JavaScript code to execute (e.g., '1 + 2', 'Math.sqrt(16)')",
                },
                "show_console": {
                    "type": "boolean",
                    "description": "Whether to include console.log/warn/error output in response (default: false)",
                    "default": True,
                },
            },
            "required": ["code"],
        }

    def _wrap_code(self, code: str) -> str:
        """包装代码以支持 return 语句。"""
        # 检测代码中是否包含 return 语句
        stripped = code.strip()
        if 'return' in code:
            # 如果已经有 IIFE 包装，不再重复包装
            if stripped.startswith('(function') or stripped.startswith('function'):
                return code
            # 包装在立即执行函数中
            return f'(function(){{\n{code}\n}})()'
        return code

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 JavaScript 代码。"""
        code = kwargs.get('code')
        show_console = kwargs.get('show_console', False)

        if not code:
            raise ValueError("JavaScript code is required")

        # 清空之前的 console 输出并重新注册函数（引用新列表）
        self._console_output = []
        self._register_console_functions()

        # 包装代码以支持 return 语句
        wrapped_code = self._wrap_code(code)

        try:
            ctx = self._get_context()
            result = ctx.eval(wrapped_code)

            # 获取结果值
            if hasattr(result, 'value'):
                value = result.value
            else:
                value = result

            # 尝试转换为 Python 对象便于序列化
            if isinstance(value, quickjs.Object):
                try:
                    json_val = value.json
                    if callable(json_val):
                        json_val = json_val()
                    # 解析 JSON 字符串为 Python 对象
                    if isinstance(json_val, str):
                        import json as pyjson
                        value = pyjson.loads(json_val)
                    else:
                        value = json_val
                except Exception:
                    pass

            result_type = self._get_js_type(value)

            response: Dict[str, Any] = {
                "code": wrapped_code if code != wrapped_code else code,
                "result": value,
                "result_type": result_type,
            }

            # 只有 show_console 为 True 时才添加 console 输出
            if show_console and self._console_output:
                response["console"] = self._console_output

            return response

        except quickjs.JSException as e:
            raise ValueError(f"JavaScript error: {str(e)}")
        except SyntaxError as e:
            raise ValueError(f"JavaScript syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"JavaScript execution failed: {str(e)}")

    async def ainvoke(self, **kwargs) -> Dict[str, Any]:
        """异步执行 JavaScript 代码。

        默认实现调用 execute 方法（已在线程池中运行）。
        子类可以重写此方法以支持真正的异步执行。

        Args:
            **kwargs: 工具参数，支持 code 和 show_console

        Returns:
            包含 code, result, result_type 的字典

        Raises:
            ValueError: 代码为空或执行失败
        """
        # 使用默认的 BaseTool.ainvoke，它会在线程池中调用 execute
        return await super().ainvoke(**kwargs)

    def __repr__(self) -> str:
        return f"QuickJSTool(name={self.name})"
