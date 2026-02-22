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
    DynamicTool
)
from src.utils.logger import get_logger

logger = get_logger("src.tools.registry_init")

# 系统工具类列表（供自动注册和 API 校验使用）
SYSTEM_TOOL_CLASSES = [
    DateTimeTool,
    CalculatorTool,
    ReadFileTool,
    SkillTool,
    BashTool,
    QuickJSTool,
    HttpTool,
]

# 从系统工具类中提取名称集合（供 API 校验使用）
SYSTEM_TOOL_NAMES = {cls().name for cls in SYSTEM_TOOL_CLASSES}

def _register_builtins() -> None:
    """注册所有内置工具。"""
    for tool_cls in SYSTEM_TOOL_CLASSES:
        register_tool(tool_cls())


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


        # 逐个注册动态工具
        for tool in active_tools:
            dynamic_tool = DynamicTool(tool)
            try:
                register_tool(dynamic_tool)
                logger.info(f"[INFO] Registered dynamic tool: {tool.name}")
            except ValueError as e:
                # 工具已存在则跳过（可能内置工具已注册）
                logger.warning(f"[WARN] Skip dynamic tool '{tool.name}': {e}")

    except Exception as e:
        # 数据库未初始化或连接失败，静默跳过
        logger.warning(f"[WARN] Failed to register dynamic tools: {e}")


# 模块导入时自动注册
_register_builtins()
_register_dynamic_tools()
