"""QuickJS 工具调用模块。

提供 callTool 函数，允许从 JavaScript 调用系统注册的工具。
"""

import json
from typing import Any, Dict

from src.tools.registry import get_registry
from src.utils.tool_args_utils import fill_default_args


def apply(ctx):
    """应用工具调用函数到 QuickJS 上下文。

    Args:
        ctx: QuickJS 上下文
    """
    def _call_tool(tool_name: str, args_json: str) -> Dict[str, Any]:
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
            return {
                "error": "ToolNotFound",
                "tool": tool_name,
                "message": f"Tool '{tool_name}' not found",
                "available": available
            }

        # 解析 JSON 字符串
        try:
            args = json.loads(args_json) if args_json else {}

        except json.JSONDecodeError as e:
            return {
                "error": "InvalidArgs",
                "tool": tool_name,
                "message": f"Invalid JSON arguments: {str(e)}"
            }

        # 获取工具 schema 并填充默认值
        tool_schema = tool.get_parameters() 
        args = fill_default_args(tool_schema, args)

        # 执行工具
        try:
            result = tool.invoke(**args)
            return result
        except Exception as e:
            return {
                "error": "ToolError",
                "tool": tool_name,
                "message": str(e)
            }

    # 注册函数（用 lambda 包装，返回 JSON 字符串）
    ctx.add_callable("_callTool", lambda name, args: json.dumps(_call_tool(name, args), ensure_ascii=False))

    # 定义 JS 辅助函数（自动 stringify 并 parse 结果）
    ctx.eval("""
        function callTool(name, args) {
            if (typeof args === 'object') {
                args = JSON.stringify(args);
            }
            var result = _callTool(name, args);
            // 尝试解析为 JSON
            try {
                var parsed = JSON.parse(result);
                // 检查是否为错误响应
                if (parsed && parsed.error) {
                    var msg = parsed.message || parsed.error;
                    throw new Error(msg);
                }
                return parsed;
            } catch (e) {
                // 解析失败，返回原始字符串
                return result;
            }
        }
    """)
