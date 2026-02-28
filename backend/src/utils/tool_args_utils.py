"""工具参数工具模块。

提供工具参数默认值填充等功能。
"""

from typing import Any, Dict


def fill_object_defaults(obj_schema: Dict[str, Any], obj_value: Any) -> Any:
    """递归填充对象中缺失的默认值。

    Args:
        obj_schema: 对象的 JSON Schema（包含 properties 定义）
        obj_value: 对象的实际值

    Returns:
        填充默认值后的对象
    """
    if not isinstance(obj_value, dict):
        return obj_value

    # 如果 schema 有 default 对象，先用默认值作为基础，再用传入值覆盖
    if "default" in obj_schema and isinstance(obj_schema["default"], dict):
        result = dict(obj_schema["default"])
        result.update(obj_value)
    else:
        result = dict(obj_value)

    properties = obj_schema.get("properties", {})
    if not properties:
        return result

    for prop_name, prop_schema in properties.items():
        if prop_name not in result:
            # 字段不存在，使用默认值
            if "default" in prop_schema:
                result[prop_name] = prop_schema["default"]
        elif isinstance(result[prop_name], dict):
            # 字段存在且是对象，递归填充
            if "properties" in prop_schema or "default" in prop_schema:
                result[prop_name] = fill_object_defaults(prop_schema, result[prop_name])

    return result


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

        # 嵌套对象示例
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "options": {
        ...             "type": "object",
        ...             "properties": {
        ...                 "a": {"type": "integer"},
        ...                 "b": {"type": "integer", "default": 10}
        ...             }
        ...         }
        ...     }
        ... }
        >>> args = {"options": {"a": 5}}
        >>> fill_default_args(schema, args)
        {"options": {"a": 5, "b": 10}}
    """

    if not tool_schema:
        return tool_args

    properties = tool_schema.get("properties", {})
    if not properties:
        return tool_args


    result = dict(tool_args)

    for param_name, param_schema in properties.items():
        if param_name not in result:
            # 参数完全不存在，使用默认值
            if "default" in param_schema:
                result[param_name] = param_schema["default"]
        elif isinstance(result[param_name], dict):
            # 参数存在且是对象，根据 schema 递归填充
            if "properties" in param_schema or "default" in param_schema:
                result[param_name] = fill_object_defaults(param_schema, result[param_name])

    return result
