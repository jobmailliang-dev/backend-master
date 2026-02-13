"""工具注册初始化。

在模块导入时注册内置工具。
"""

from src.tools.registry import register_tool
from src.tools.builtins import (
    DateTimeTool,
    CalculatorTool,
    ReadFileTool,
    SkillTool,
    BashTool,
    QuickJSTool,
    HttpTool,
)


def _register_builtins() -> None:
    """注册所有内置工具。"""
    register_tool(DateTimeTool())
    register_tool(CalculatorTool())
    register_tool(ReadFileTool())
    register_tool(SkillTool())
    register_tool(BashTool())
    register_tool(QuickJSTool())
    register_tool(HttpTool())


# 模块导入时自动注册
_register_builtins()
