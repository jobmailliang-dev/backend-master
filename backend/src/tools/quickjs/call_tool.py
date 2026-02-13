"""QuickJS 工具调用模块。

提供 callTool 函数，允许从 JavaScript 调用系统注册的工具。
"""

import json
from typing import Any

from src.tools.registry import get_registry


def apply(ctx):
    """应用工具调用函数到 QuickJS 上下文。

    Args:
        ctx: QuickJS 上下文
    """
    def _call_tool(tool_name: str, args_json: str) -> str:
        """从 JavaScript 调用系统工具。

        Args:
            tool_name: 工具名称
            args_json: 工具参数的 JSON 字符串

        Returns:
            JSON 格式的工具执行结果

        Raises:
            ValueError: 工具不存在或参数错误
        """
        registry = get_registry()

        # 检查工具是否存在
        tool = registry.get(tool_name)
        if tool is None:
            available = registry.list_all()
            # 返回包含详细错误信息的 JSON
            return json.dumps({
                "error": "ToolNotFound",
                "tool": tool_name,
                "message": f"Tool '{tool_name}' not found",
                "available": available
            }, ensure_ascii=False)

        # 解析 JSON 字符串
        try:
            args = json.loads(args_json) if args_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "InvalidArgs",
                "tool": tool_name,
                "message": f"Invalid JSON arguments: {str(e)}"
            }, ensure_ascii=False)

        # 执行工具
        try:
            result = registry.execute(tool_name, **args)
            return result
        except Exception as e:
            return json.dumps({
                "error": "ToolError",
                "tool": tool_name,
                "message": str(e)
            }, ensure_ascii=False)

    # 注册原始函数
    ctx.add_callable("_callTool", _call_tool)

    # 定义 JS 辅助函数（自动 stringify 并 parse 结果）
    ctx.eval("""
        function callTool(name, args) {
            if (typeof args === 'object') {
                args = JSON.stringify(args);
            }
            var result = _callTool(name, args);
            if (typeof result === 'string') {
                var parsed = JSON.parse(result);
                // 检查是否为错误响应
                if (parsed && parsed.error) {
                    var msg = parsed.message || parsed.error;
                    if (parsed.available) {
                        msg += ' [Available: ' + parsed.available.join(', ') + ']';
                    }
                    throw new Error(msg);
                }
                return parsed;
            }
            // 非字符串结果直接返回
            return result;
        }
    """)
