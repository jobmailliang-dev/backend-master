"""QuickJS 工具。

执行 JavaScript 代码并返回结果。
"""

import asyncio
import json
import json as pyjson
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from functools import partial

import quickjs  # pyright: ignore[reportImplicitRelativeImport]

from src.tools.base import BaseTool
from src.tools.quickjs.func_console import apply as apply_console
from src.tools.quickjs.call_tool import apply as apply_call_tool
from src.tools.quickjs.sse_push import apply as apply_sse_push
from src.tools.quickjs.dict_proxy import DictProxy, DictProxyManager


class QuickJSTool(BaseTool):
    """JavaScript 执行工具。

    使用 ThreadLocal 为每个线程创建独立的 JS Context，
    并通过独立线程池执行 eval，确保脚本执行完全隔离。
    """

    # 线程池大小，可根据需要调整
    MAX_WORKERS = 4

    def __init__(self):
        """初始化 QuickJS 工具。"""
        super().__init__(
            name="quickjs",
            description="Execute JavaScript code and return the result",
        )
        # ThreadLocal: 每个线程独立的 Context
        self._thread_local = threading.local()
        # 全局代理管理器（线程共享）
        self._proxy_manager: DictProxyManager = DictProxyManager()
        # 独立线程池执行 eval
        self._executor = ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS,
            thread_name_prefix="quickjs_eval_"
        )

    def _get_context(self) -> quickjs.Context:
        """获取当前线程的 Context（线程隔离）。

        每个线程首次调用时创建独立的 Context。
        """
        if not hasattr(self._thread_local, 'context'):
            # 创建新 Context
            self._thread_local.context = quickjs.Context()
            self._thread_local.console_setup = False
            # 标记该线程的 Context 需要注册回调
            self._thread_local.callbacks_registered = False

        return self._thread_local.context

    def _ensure_callbacks_registered(self, ctx: quickjs.Context) -> None:
        """确保回调已注册到 Context。

        每个线程的 Context 只需要注册一次回调。
        """
        thread_local = self._thread_local

        if not getattr(thread_local, 'callbacks_registered', False):
            # 注册 dict proxy 回调
            self._register_dict_proxy_callbacks(ctx)
            thread_local.callbacks_registered = True

    def _register_dict_proxy_callbacks(self, ctx: quickjs.Context) -> None:
        """注册 dict 代理的回调函数到指定 Context。"""
        # 注册 dict 操作回调
        ctx.add_callable("_dictGet", self._js_dict_get)
        ctx.add_callable("_dictSet", self._js_dict_set)
        ctx.add_callable("_dictHas", self._js_dict_has)
        ctx.add_callable("_dictKeys", self._js_dict_keys)
        ctx.add_callable("_dictDelete", self._js_dict_delete)
        ctx.add_callable("_createNestedProxy", self._js_create_nested_proxy)

    def _setup_dict_proxy(self) -> None:
        """设置 dict 代理的回调函数（兼容旧接口）。"""
        ctx = self._get_context()
        if ctx is None:
            return
        self._ensure_callbacks_registered(ctx)

    def _js_dict_get(self, obj_id: str, key: str) -> Any:
        """JS 端 getter 回调。"""
        proxy = self._proxy_manager.get(obj_id)
        if not proxy:
            return None
        value = proxy.get(key)
        # 如果返回的是 DictProxy，需要将其注册到 manager 中
        if isinstance(value, DictProxy):
            # 直接使用原有的 DictProxy 对象注册到 manager
            if not self._proxy_manager.get(value.obj_id):
                self._proxy_manager._proxies[value.obj_id] = value
            # 返回特殊标记格式
            return f"__PROXY:{value.obj_id}__"
        if isinstance(value, list):
            # 列表中的嵌套 dict 需要特殊处理
            # 注意：由于 quickjs add_callable 无法直接返回 JS 数组，
            # 我们返回 JSON 字符串，JS 端需要解析
            import json as pyjson
            result = []
            for item in value:
                if isinstance(item, DictProxy):
                    # 直接使用原有的 DictProxy 对象
                    if not self._proxy_manager.get(item.obj_id):
                        self._proxy_manager._proxies[item.obj_id] = item
                    result.append({"__proxy": item.obj_id})
                else:
                    result.append(item)
            return pyjson.dumps(result)
        return value

    def _js_dict_set(self, obj_id: str, key: str, value: Any) -> None:
        """JS 端 setter 回调。"""
        proxy = self._proxy_manager.get(obj_id)
        if proxy:
            proxy.set(key, value)
        return None

    def _js_dict_has(self, obj_id: str, key: str) -> str:
        """JS 端 has 检查回调。

        返回字符串 "true"/"false" 以便 JS 端正确处理
        """
        proxy = self._proxy_manager.get(obj_id)
        return "true" if (proxy.has(key) if proxy else False) else "false"

    def _js_dict_keys(self, obj_id: str) -> str:
        """JS 端 keys 获取回调。

        返回 JSON 字符串，JS 端需要 JSON.parse 解析
        """
        import json as pyjson
        proxy = self._proxy_manager.get(obj_id)
        keys = proxy.keys() if proxy else []
        return pyjson.dumps(keys)

    def _js_dict_delete(self, obj_id: str, key: str) -> bool:
        """JS 端 delete 操作回调。"""
        proxy = self._proxy_manager.get(obj_id)
        return proxy.delete(key) if proxy else False

    def _js_create_nested_proxy(self, obj_id: str) -> Any:
        """创建嵌套代理的回调。"""
        proxy = self._proxy_manager.get(obj_id)
        if not proxy:
            return None
        # 返回代理 ID，JS 端会创建 Proxy 包装
        return {"__proxy_id": obj_id}

    def _to_js_value(self, value: Any) -> Any:
        """Python 值转换为 JS 可用值。

        Args:
            value: Python 值

        Returns:
            转换后的值，dict 会转为包含 __proxy_id 的对象
        """
        if isinstance(value, DictProxy):
            # 返回代理 ID，JS 端会通过 Proxy 拦截
            return {"__proxy_id": value.obj_id}
        if isinstance(value, list):
            return [self._to_js_value(item) for item in value]
        return value

    def _create_js_proxy(self, ctx: quickjs.Context, obj_id: str) -> Any:
        """在指定 Context 中创建 JS Proxy 对象。"""
        proxy_code = f"""
        (function() {{
            const objId = '{obj_id}';
            const createProxy = function(nestedObjId) {{
                return new Proxy({{}}, {{
                    get: function(target, prop) {{
                        if (prop === '__objId__') return nestedObjId;
                        if (prop === '_isProxy') return true;
                        let result = _dictGet(nestedObjId, prop);
                        // 检查是否返回的是 JSON 字符串（数组情况）
                        if (typeof result === 'string' && result.startsWith('[')) {{
                            try {{
                                const arr = JSON.parse(result);
                                return arr.map(function(item) {{
                                    if (item && item.__proxy) {{
                                        return createProxy(item.__proxy);
                                    }}
                                    return item;
                                }});
                            }} catch(e) {{ return result; }}
                        }}
                        // 检查是否是嵌套代理标记
                        if (typeof result === 'string' && result.startsWith('__PROXY:')) {{
                            const nestedId = result.slice(8, -2);
                            return createProxy(nestedId);
                        }}
                        return result;
                    }},
                    set: function(target, prop, value) {{
                        _dictSet(nestedObjId, prop, value);
                        return true;
                    }},
                    has: function(target, prop) {{
                        return _dictHas(nestedObjId, prop) === 'true';
                    }},
                    deleteProperty: function(target, prop) {{
                        return _dictDelete(nestedObjId, prop);
                    }},
                    ownKeys: function(target) {{
                        return JSON.parse(_dictKeys(nestedObjId));
                    }},
                    getOwnPropertyDescriptor: function(target, prop) {{
                        return {{
                            enumerable: true,
                            configurable: true,
                            value: this.get(target, prop)
                        }};
                    }}
                }});
            }};
            const proxy = createProxy(objId);
            return proxy;
        }})()
        """
        return ctx.eval(proxy_code)

    def expose_dict(self, py_dict: dict, name: str = None) -> str:
        """暴露 Python dict 到 JS 环境。

        Args:
            py_dict: 要暴露的 Python 字典
            name: 可选的变量名

        Returns:
            JS 环境中的变量名

        Example:
            >>> tool = QuickJSTool()
            >>> data = {"name": "Alice", "age": 30}
            >>> var_name = tool.expose_dict(data, "userData")
            >>> tool.eval("userData.name = 'Bob'")
            >>> print(data["name"])  # 输出: "Bob"
        """
        ctx = self._get_context()
        # 确保回调已注册
        self._ensure_callbacks_registered(ctx)

        obj_id = self._proxy_manager.create(py_dict, name)

        # 在 JS 中创建 Proxy 对象
        js_proxy = self._create_js_proxy(ctx, obj_id)

        # 使用固定变量名
        var_name = name or f"exposed_dict_{obj_id}"
        ctx.set(var_name, js_proxy)

        return var_name

    def release_dict(self, name: str) -> bool:
        """释放已暴露的 dict。

        Args:
            name: expose_dict 返回的变量名

        Returns:
            是否成功释放

        Example:
            >>> tool.release_dict("userData")
        """
        if self._proxy_manager.release(name):
            ctx = self._get_context()
            # 使用 eval 删除全局变量
            ctx.eval(f"delete globalThis.{name}")
            return True
        return False

    def get_dict(self, name: str) -> Optional[dict]:
        """获取暴露后 dict 的原始引用。

        Args:
            name: expose_dict 返回的变量名

        Returns:
            原始 Python dict 引用

        Example:
            >>> tool.expose_dict(data, "userData")
            >>> tool.eval("userData.name = 'Bob'")
            >>> print(tool.get_dict("userData"))  # {'name': 'Bob', ...}
        """
        proxy = self._proxy_manager.get(name)
        return proxy.to_dict() if proxy else None

    def _register_console_functions(self) -> None:
        """注册 console 和工具调用函数到当前线程的 Context。"""
        ctx = self._get_context()
        thread_local = self._thread_local

        if not getattr(thread_local, 'console_setup', False):
            apply_console(ctx)
            apply_call_tool(ctx)
            apply_sse_push(ctx)
            thread_local.console_setup = True

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
            },
            "required": ["code"],
        }

    def _wrap_code(self, code: str) -> str:
        """包装代码以支持 return 语句。"""
        stripped = code.strip()
        if 'return' in code:
            # 判断是否已经是 IIFE 包装：以 ( 开头且以 )() 结尾
            is_iife = stripped.startswith('(') and stripped.rstrip().endswith(')()')
            if is_iife:
                return code
            # 包装在立即执行函数中
            return f'(function(){{\n{code}\n}})()'
        return code

    def _eval_in_thread(self, wrapped_code: str) -> Any:
        """在线程池中执行 eval。

        这是真正在独立线程中执行的逻辑。
        确保所有异常都在线程内捕获，不会泄漏到主线程。
        """
        ctx = self._get_context()
        # 确保回调已注册
        self._ensure_callbacks_registered(ctx)

        try:
            result = ctx.eval(wrapped_code)
            return result
        except Exception:
            # 重新抛出，由调用方处理
            raise

    def invoke(self, **kwargs) -> Dict[str, Any]:
        """执行 JavaScript 代码（同步版本）。

        实际执行在线程池中进行，确保隔离。

        Args:
            **kwargs: 支持以下参数:
                - code: JavaScript 代码 (必需)
                - tool_name: 工具名称
                - context: 可选的 context 字典

        Returns:
            包含 code, result, result_type 的字典
        """
        code = kwargs.get('code')
        tool_name = kwargs.get('tool_name', self.name)
        context = kwargs.get('context')
        if not code:
            raise ValueError("JavaScript code is required")

        wrapped_code = self._wrap_code(code)

        # 同步调用 _execute_in_thread（它会在线程池的线程中执行）
        from concurrent.futures import Future
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop:
            # 在已有事件循环中，使用线程池
            future = loop.run_in_executor(
                self._executor,
                partial(
                    self._execute_in_thread,
                    code=wrapped_code,
                    original_code=code,
                    tool_name=tool_name,
                    context=context
                )
            )
            # 注意：这里不能 await，因为 invoke 是同步方法
            # 所以需要用不同的方式

        # 简化：直接调用（在当前线程执行，但有 ThreadLocal 隔离）
        return self._execute_in_thread(
            code=wrapped_code,
            original_code=code,
            tool_name=tool_name,
            context=context
        )
        # _execute_in_thread 已经处理了所有异常和清理

    async def ainvoke(self, **kwargs) -> Dict[str, Any]:
        """异步执行 JavaScript 代码。

        使用独立线程池执行 eval，确保脚本执行完全隔离。
        任何错误都不会导致主线程崩溃。

        Args:
            **kwargs: 工具参数，支持 code, name, timeout
                - code: JavaScript 代码 (必需)
                - tool_name: 工具名称
                - context: 可选的 context 字典
                - timeout: 超时时间（秒），默认 30 秒

        Returns:
            包含 code, result, result_type 的字典

        Raises:
            ValueError: 代码为空或执行失败
            TimeoutError: 脚本执行超时
        """
        code = kwargs.get('code')
        tool_name = kwargs.get('tool_name', self.name)
        context = kwargs.get('context')
        if not code:
            raise ValueError("JavaScript code is required")

        # 包装代码以支持 return 语句
        wrapped_code = self._wrap_code(code)

        # 将所有操作都放到线程池中执行（确保 Context 一致）
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self._executor,
                partial(
                    self._execute_in_thread,
                    code=wrapped_code,
                    original_code=code,
                    tool_name=tool_name,
                    context=context
                )
            )
            return result
        except Exception as e:
            raise ValueError(f"JavaScript execution failed: {str(e)}")

    def _execute_in_thread(
        self,
        code: str,
        original_code: str,
        tool_name: str,
        context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """在线程池中执行完整的 JS 操作流程。

        确保 expose_dict 和 eval 使用同一个 Context。
        """
        # 获取当前线程的 Context（ThreadLocal 隔离）
        ctx = self._get_context()

        # 设置工具名称
        ctx.set("_tool_name", tool_name)

        # 注册 console 函数
        thread_local = self._thread_local
        if not getattr(thread_local, 'console_setup', False):
            apply_console(ctx)
            apply_call_tool(ctx)
            apply_sse_push(ctx)
            thread_local.console_setup = True

        # 确保 dict proxy 回调已注册
        self._ensure_callbacks_registered(ctx)

        # 如果提供了 context，使用 expose_dict 注册到 JS 环境
        # 使用唯一的变量名来避免并发冲突，但最终在 JS 中使用 "context" 这个名称
        context_var_name = None
        if context:
            # 不指定名称，让它生成唯一的 obj_id
            unique_var_name = self.expose_dict(context)
            # 将变量重命名为 "context"
            ctx.eval(f"var context = {unique_var_name}")
            context_var_name = unique_var_name

        try:
            # 执行 eval
            result = ctx.eval(code)

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

            return {
                "code": code if code != original_code else original_code,
                "result": value,
                "result_type": result_type,
            }

        except quickjs.JSException as e:
            raise ValueError(f"JavaScript error: {str(e)}")
        except SyntaxError as e:
            raise ValueError(f"JavaScript syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"JavaScript execution failed: {str(e)}")
        finally:
            # 执行结束后释放 context
            if context_var_name:
                self.release_dict(context_var_name)

    def _safe_eval(self, wrapped_code: str) -> Any:
        """在线程池中安全执行 eval。

        确保所有异常都在线程内捕获，不会泄漏到主线程。
        """
        ctx = self._get_context()
        # 确保回调已注册
        self._ensure_callbacks_registered(ctx)

        try:
            result = ctx.eval(wrapped_code)
            return result
        except quickjs.JSException as e:
            # 转换为 ValueError，避免跨线程传播
            raise ValueError(f"JavaScript error: {str(e)}")
        except SyntaxError as e:
            raise ValueError(f"JavaScript syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"JavaScript execution failed: {str(e)}")

    def __repr__(self) -> str:
        return f"QuickJSTool(name={self.name})"
