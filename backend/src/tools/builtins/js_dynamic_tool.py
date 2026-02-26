
"""动态工具类 - 从数据库加载的工具"""

from typing import Any, Dict, Optional

from src.tools.base import BaseTool
from src.modules.tools.models import Tool
from src.tools.quickjs.quickjs_tool import QuickJSTool
from src.utils.script_wrapper import wrap_javascript_code
from src.core.session_context import get_session


class DynamicTool(BaseTool):
    """动态工具 - 包装数据库中的 Tool 实体"""

    def __init__(self, tool: Tool):
        """初始化动态工具。

        Args:
            tool: 数据库中的 Tool 实体
        """
        super().__init__(tool.name, tool.description)
        self._tool = tool

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        params = self._tool.parameters

        if not params:
            # 如果没有自定义参数，返回空对象
            return {"type": "object", "properties": {}}

        # 转换为 JSON Schema 格式
        properties = {}
        required = []
        for p in params:
            prop: Dict[str, Any] = {
                "type": p.type,
                "description": p.description
            }
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop

            if p.required:
                required.append(p.name)

        result: Dict[str, Any] = {
            "type": "object",
            "properties": properties
        }
        if required:
            result["required"] = required

        return result

    def invoke(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具。

        使用 wrap_javascript_code 包装代码，然后调用 quickjs 工具执行。

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典
        """
        # 从 session 获取 metadata
        metadata: Dict[str, Any] = {}
        session = get_session()
        if session:
            metadata = session._metadata

        # 包装 JavaScript 脚本，获取 context 和 script
        context, script = wrap_javascript_code(
            self._tool.code,
            kwargs,
            metadata=metadata,
            inherit_from=self._tool.inherit_from
        )
        # 创建新的 QuickJSTool 实例，避免线程安全问题
        tool = QuickJSTool()

        # 将 context 传给 quickjs 工具，内部会自动暴露和释放
        result = tool.invoke(code=script, tool_name=self._tool.name, context=context)

        # 直接返回结果
        return result["result"]

    async def ainvoke(self, **kwargs: Any) -> Dict[str, Any]:
        """异步执行工具。

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典
        """
        # 从 session 获取 metadata
        metadata: Optional[Dict[str, Any]] = None
        session = get_session()
        if session:
            metadata = session._metadata

        # 包装 JavaScript 脚本，获取 context 和 script
        context, script = wrap_javascript_code(
            self._tool.code,
            kwargs,
            metadata=metadata,
            inherit_from=self._tool.inherit_from
        )

        # 创建新的 QuickJSTool 实例，避免线程安全问题
        tool = QuickJSTool()
        # 将 context 传给 quickjs 工具，内部会自动暴露和释放
        result = await tool.ainvoke(code=script, tool_name=self._tool.name, context=context)

        # 直接返回结果
        return result["result"]
