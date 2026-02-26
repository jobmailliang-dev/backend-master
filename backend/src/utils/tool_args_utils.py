"""工具参数工具模块。

提供工具参数默认值填充等功能。
"""

from typing import Any, Dict


def fill_default_args(tool_schema: Dict[str, Any], tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """使用工具参数的默认值填充未赋值的参数。

    Args:
        tool_schema: 工具的 JSON Schema 定义
        tool_args: LLM 返回的工具参数

    Returns:
        填充默认值后的工具参数

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "command": {"type": "string"},
        ...         "timeout": {"type": "integer", "default": 60}
        ...     }
        ... }
        >>> args = {"command": "ls"}
        >>> fill_default_args(schema, args)
        {"command": "ls", "timeout": 60}
    """

    print(f"fill_default_args===={tool_schema}====={tool_args}")

    if not tool_schema:
        return tool_args

    properties = tool_schema.get("properties", {})
    if not properties:
        return tool_args

    result = dict(tool_args)

    for param_name, param_schema in properties.items():
        # 如果参数未在 tool_args 中，且有默认值，则填充
        if param_name not in result:
            if "default" in param_schema:
                result[param_name] = param_schema["default"]

    return result
