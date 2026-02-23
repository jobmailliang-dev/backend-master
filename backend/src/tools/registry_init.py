"""工具注册初始化。

在模块导入时注册内置工具和 MCP 工具。
"""

import os
import asyncio
import threading
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
from src.tools.mcp import register_mcp_servers

logger = get_logger(__name__)

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
        try:
            register_tool(tool_cls())
        except ValueError as e:
            logger.warning(f"[WARN] Failed to register builtin tool: {e}")


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
                logger.info(f"Registered dynamic tool: {tool.name}")
            except ValueError as e:
                # 工具已存在则跳过（可能内置工具已注册）
                logger.warning(f"Skip dynamic tool '{tool.name}': {e}")

    except Exception as e:
        # 数据库未初始化或连接失败，静默跳过
        logger.warning(f"Failed to register dynamic tools: {e}")


def _register_mcp_tools() -> None:
    """注册 MCP 工具（如果已配置）。

    使用并发方式注册所有 MCP 服务器的工具。
    """
    try:
        # 获取全局注册表
        from src.tools.registry import get_registry

        # 获取项目根目录
        project_root = os.environ.get("PROJECT_ROOT", os.getcwd())

        # 注册 MCP 服务器工具（并发方式）
        clients, registered_tools = register_mcp_servers(get_registry(), project_root)

        if registered_tools:
            logger.info(f"[INFO] Registered {len(registered_tools)} MCP tools")

    except ImportError as e:
        # MCP 依赖未安装，静默跳过
        logger.warning(f"[WARN] MCP dependencies not installed: {e}")
    except Exception as e:
        # MCP 配置错误或其他异常
        logger.warning(f"[WARN] Failed to register MCP tools: {e}")


def _run_mcp_registration():
    """在独立线程中运行 MCP 工具注册（不阻塞主线程）。

    使用独立线程运行事件循环，避免阻塞模块导入。
    """
    
    def _thread_target():
        """线程目标函数。"""
        """异步注册任务。"""
        try:
            _register_mcp_tools()
        except Exception as e:
            logger.warning(f"[WARN] MCP registration error: {e}")


    # 创建并启动后台线程
    thread = threading.Thread(target=_thread_target, daemon=True, name="MCP-Registration")
    thread.start()
    logger.info("[INFO] MCP tools registration started in background thread")


# 模块导入时自动注册
_register_builtins()
_register_dynamic_tools()

# 注册 MCP 工具（异步多线程方式）
_run_mcp_registration()
