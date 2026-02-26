"""QuickJS SSE 推送模块。

提供 ssePush 函数，允许从 JavaScript 推送内容到 SSE 流。
"""

import json

from src.utils.stream_writer_util import send_queue, task_context


def apply(ctx, tool_name: str = None):
    """应用 SSE 推送函数到 QuickJS 上下文。

    Args:
        ctx: QuickJS 上下文
        tool_name: 工具名称（用于日志推送），如果为 None 则从 ctx.globals 获取
    """
    # 从 context 中获取 tool_name，避免线程安全问题
    if tool_name is None:
        try:
            tool_name = ctx.get("_tool_name")
            if tool_name is None:
                tool_name = "quickjs"
        except Exception:
            tool_name = "quickjs"

    def _sse_push(event: str, data) -> bool:
        """推送内容到 SSE 流。

        Args:
            event: 事件名称，如 "content", "console", "done", "error" 等
            data: 要发送的数据（可以是字符串或对象）

        Returns:
            bool: 是否成功推送
        """
        try:
            context = task_context.get()
            if context and context.get("stream_writer") is not None:
                # 如果 data 是对象，转换为 JSON 字符串
                if not isinstance(data, str):
                    data = json.dumps(data, ensure_ascii=False)
                send_queue(data, event)
                return True
            return False
        except Exception:
            return False

    # 使用 add_callable 注册 Python 函数
    ctx.add_callable("_ssePush", _sse_push)

    # 在 JS 中定义 ssePush 函数，调用注册的 Python 函数
    ctx.eval("""
        function ssePush(event, data) {
            // 如果 data 是对象，转换为 JSON 字符串
            if (typeof data === 'object' && data !== null) {
                data = JSON.stringify(data);
            }
            return _ssePush(event, data);
        }

        // 便捷方法：推送内容到指定事件
        function pushContent(content) {
            return ssePush("content", content);
        }

        function pushConsole(message) {
            return ssePush("console", message);
        }

        function pushDone() {
            return ssePush("done", "");
        }

        function pushError(error) {
            return ssePush("error", error);
        }
    """)
