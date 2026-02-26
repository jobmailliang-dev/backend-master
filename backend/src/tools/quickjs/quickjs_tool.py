"""QuickJS 工具。

执行 JavaScript 代码并返回结果。
"""

import asyncio
import json as pyjson
from typing import Any, Dict, List, Optional

import quickjs  # pyright: ignore[reportImplicitRelativeImport]

from src.tools.base import BaseTool
from src.tools.quickjs.func_console import apply as apply_console
from src.tools.quickjs.call_tool import apply as apply_call_tool
from src.tools.quickjs.dict_proxy import DictProxy, DictProxyManager


class QuickJSTool(BaseTool):
    """JavaScript 执行工具。"""

    def __init__(self):
        """初始化 QuickJS 工具。"""
        super().__init__(
            name="quickjs",
            description="Execute JavaScript code and return the result",
        )
        self._context: quickjs.Context | None = None
        self._proxy_manager: DictProxyManager = DictProxyManager()
        self._dict_proxy_setup: bool = False

    def _get_context(self) -> quickjs.Context:
        """获取或创建 JS 上下文。"""
        if self._context is None:
            self._context = quickjs.Context()
        # 确保 dict proxy 函数已注册
        if not self._dict_proxy_setup:
            self._setup_dict_proxy()
        return self._context

    def _setup_dict_proxy(self) -> None:
        """设置 dict 代理的回调函数。"""
        ctx = self._context
        if ctx is None:
            return

        # 注册 dict 操作回调
        ctx.add_callable("_dictGet", self._js_dict_get)
        ctx.add_callable("_dictSet", self._js_dict_set)
        ctx.add_callable("_dictHas", self._js_dict_has)
        ctx.add_callable("_dictKeys", self._js_dict_keys)
        ctx.add_callable("_dictDelete", self._js_dict_delete)
        ctx.add_callable("_createNestedProxy", self._js_create_nested_proxy)

        self._dict_proxy_setup = True

    def _js_dict_get(self, obj_id: str, key: str) -> Any:
        """JS 端 getter 回调。"""
        proxy = self._proxy_manager.get(obj_id)
        if not proxy:
            return None
        value = proxy.get(key)
        # 如果返回的是 DictProxy，需要将其注册到 manager 中
        if isinstance(value, DictProxy):
            # 检查是否已经注册，如果没有则注册
            if not self._proxy_manager.get(value.obj_id):
                # 创建新的代理数据包装并注册
                nested_data = value.to_dict()
                # 使用相同的 obj_id 注册
                self._proxy_manager._proxies[value.obj_id] = DictProxy(nested_data, value.obj_id)
            # 返回特殊标记格式
            return f"__PROXY:{value.obj_id}__"
        if isinstance(value, list):
            # 列表中的嵌套 dict 需要特殊处理
            result = []
            for item in value:
                if isinstance(item, DictProxy):
                    # 检查是否已经注册
                    if not self._proxy_manager.get(item.obj_id):
                        nested_data = item.to_dict()
                        self._proxy_manager._proxies[item.obj_id] = DictProxy(nested_data, item.obj_id)
                    result.append(f"__PROXY:{item.obj_id}__")
                else:
                    result.append(item)
            return result
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
        obj_id = self._proxy_manager.create(py_dict, name)

        # 在 JS 中创建 Proxy 对象
        proxy_code = f"""
        (function() {{
            const objId = '{obj_id}';
            const createProxy = function(nestedObjId) {{
                return new Proxy({{}}, {{
                    get: function(target, prop) {{
                        if (prop === '__objId__') return nestedObjId;
                        if (prop === '_isProxy') return true;
                        const result = _dictGet(nestedObjId, prop);
                        // 检查是否是嵌套代理标记
                        if (typeof result === 'string' && result.startsWith('__PROXY:')) {{
                            const nestedId = result.slice(8, -2);
                            return createProxy(nestedId);
                        }}
                        // 检查数组中的嵌套代理
                        if (Array.isArray(result)) {{
                            return result.map(function(item) {{
                                if (typeof item === 'string' && item.startsWith('__PROXY:')) {{
                                    const nestedId = item.slice(8, -2);
                                    return createProxy(nestedId);
                                }}
                                return item;
                            }});
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

        js_proxy = ctx.eval(proxy_code)

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
        """注册 console 和工具调用函数。"""
        ctx = self._get_context()
        apply_console(ctx)
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

    def invoke(self, **kwargs) -> Dict[str, Any]:
        """执行 JavaScript 代码。

        Args:
            **kwargs: 支持以下参数:
                - code: JavaScript 代码 (必需)
                - tool_name: 工具名称
                - context: 可选的 context 字典，会通过 expose_dict 注册为 "context" 变量

        Returns:
            包含 code, result, result_type 的字典
        """
        code = kwargs.get('code')
        tool_name = kwargs.get('tool_name', self.name)
        context = kwargs.get('context')  # 可选的 context 字典
        if not code:
            raise ValueError("JavaScript code is required")

        # 清空之前的 console 输出并重新注册函数（引用新列表）
        # 将 tool_name 存储到 context globals 中，避免线程安全问题
        ctx = self._get_context()
        ctx.set("_tool_name", tool_name)
        self._register_console_functions()

        # 如果提供了 context，使用 expose_dict 注册到 JS 环境
        context_var_name = None
        if context:
            context_var_name = self.expose_dict(context, "context")

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

            return response

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

    async def ainvoke(self, **kwargs) -> Dict[str, Any]:
        """异步执行 JavaScript 代码。

        默认实现调用 execute 方法（已在线程池中运行）。
        子类可以重写此方法以支持真正的异步执行。

        Args:
            **kwargs: 工具参数，支持 code 和 name

        Returns:
            包含 code, result, result_type 的字典

        Raises:
            ValueError: 代码为空或执行失败
        """
        # 使用默认的 BaseTool.ainvoke，它会在线程池中调用 execute
        return await super().ainvoke(**kwargs)

    def __repr__(self) -> str:
        return f"QuickJSTool(name={self.name})"
