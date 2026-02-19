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


def _register_dynamic_tools() -> None:
    """从数据库加载动态工具并注册到注册表。"""
    try:
        from src.modules import get_injector, ToolDao

        # 获取 ToolDao 实例
        injector = get_injector()
        dao: ToolDao = injector.get(ToolDao)

        # 获取所有激活的工具
        active_tools = dao.get_active()

        if not active_tools:
            return

        # 导入 DynamicTool
        from src.tools.builtins.dynamic_tool import DynamicTool

        # 逐个注册动态工具
        for tool in active_tools:
            dynamic_tool = DynamicTool(tool)
            try:
                register_tool(dynamic_tool)
                print(f"[INFO] Registered dynamic tool: {tool.name}")
            except ValueError as e:
                # 工具已存在则跳过（可能内置工具已注册）
                print(f"[WARN] Skip dynamic tool '{tool.name}': {e}")

    except Exception as e:
        # 数据库未初始化或连接失败，静默跳过
        print(f"[WARN] Failed to register dynamic tools: {e}")


# 模块导入时自动注册
_register_builtins()
_register_dynamic_tools()
