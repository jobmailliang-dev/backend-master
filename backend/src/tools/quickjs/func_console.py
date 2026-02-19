"""QuickJS 控制台函数注册模块。

提供 console.log、console.warn、console.error 等函数的注册功能。
支持通过 stream_writer_util 实时推送日志到前端。
"""

import time

from src.utils.stream_writer_util import send_queue, task_context


def apply(ctx, tool_name: str = None):
    """应用控制台函数注册到 QuickJS 上下文。

    Args:
        ctx: QuickJS 上下文
        console_output_ref: 控制台输出列表的引用
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
    def _send_console_log(level: str, *args):
        """发送控制台日志到流和本地列表。"""
        # 转换参数为字符串
        output = " ".join(_js_value_to_string(arg) for arg in args)
        timestamp = time.time()

        # 通过 stream_writer 推送到前端（SSE）
        try:
            context = task_context.get()
            if context and context.get("stream_writer") is not None:
                send_queue({
                    "type": level,
                    "tool_name": tool_name,
                    "message": output,
                    "timestamp": timestamp
                }, "console")
        except Exception:
            # 如果推送失败，静默处理，不影响 JS 执行
            pass

    def console_log(*args):
        """console.log 实现"""
        _send_console_log("info", *args)
        return None

    def console_warn(*args):
        """console.warn 实现"""
        _send_console_log("warn", *args)
        return None

    def console_error(*args):
        """console.error 实现"""
        _send_console_log("error", *args)
        return None

    # 使用 add_callable 注册 Python 函数
    ctx.add_callable("console_log", console_log)
    ctx.add_callable("console_warn", console_warn)
    ctx.add_callable("console_error", console_error)

    # 在 JS 中定义 console 对象，调用注册的函数
    ctx.eval("""
        var console = {
            log: function(...args) { return console_log(...args); },
            warn: function(...args) { return console_warn(...args); },
            error: function(...args) { return console_error(...args); }
        };
    """)


def _js_value_to_string(value):
    """将 JS 值转换为字符串。"""
    import quickjs
    import json

    if value is None:
        return "null"
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, quickjs.Object):
        try:
            json_str = value.json
            if callable(json_str):
                json_str = json_str()
            return json.dumps(json_str, ensure_ascii=False)
        except Exception:
            return f"[Object: {value}]"
    else:
        return str(value)
