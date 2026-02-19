"""动态工具类 - 从数据库加载的工具"""

from typing import Any, Dict

from src.tools.base import BaseTool
from src.modules.tools.models import Tool
from src.tools.registry import get_registry
from src.utils.script_wrapper import wrap_javascript_code


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

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具。

        使用 wrap_javascript_code 包装代码，然后调用 quickjs 工具执行。

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典
        """
        # 包装 JavaScript 脚本
        script = wrap_javascript_code(
            self._tool.code,
            kwargs,
            inherit_from=self._tool.inherit_from
        )

        # 调用 quickjs 工具执行
        registry = get_registry()
        result = registry.execute("quickjs", code=script)

        # 直接返回结果
        return {"result": result}

    async def ainvoke(self, **kwargs: Any) -> Dict[str, Any]:
        """异步执行工具。

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典
        """
        # 包装 JavaScript 脚本
        script = wrap_javascript_code(
            self._tool.code,
            kwargs,
            inherit_from=self._tool.inherit_from
        )

        # 调用 quickjs 工具执行（异步）
        registry = get_registry()
        result = await registry.aexecute("quickjs", code=script)

        # 直接返回结果
        return {"result": result}
