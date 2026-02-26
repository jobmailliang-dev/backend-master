"""工具管理 API"""

import asyncio
import json
import time
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from src.api.models import ApiResponse
from src.modules import ToolService
from src.core import get_app_config, get_service
from src.modules.base import ValidException, ApiException
from src.modules.tools.dtos import ToolDto
from src.utils.logger import get_logger
from src.utils.script_wrapper import wrap_javascript_code
from src.utils.stream_writer_util import create_queue_task, send_queue
from src.tools.registry_init import SYSTEM_TOOL_NAMES

router = APIRouter(prefix="/api/tools", tags=["tools"])

# 获取日志器
_logger = get_logger(__name__)
_service = get_service(ToolService)


def _check_tool_name(name: str) -> None:
    """校验工具名称是否为系统内置工具。

    Args:
        name: 工具名称

    Raises:
        ValidException: 如果是系统内置工具
    """
    if name.lower() in SYSTEM_TOOL_NAMES:
        raise ValidException(f"工具名 '{name}' 是系统内置工具，无法创建/修改")


@router.get("")
async def get_tools(id: int = Query(default=None, description="Tool ID (optional)")):
    """获取工具列表或单个工具

    - 无 id 参数时返回所有工具列表
    - 有 id 参数时返回单个工具
    """
    
    if id is not None:
        # 获取单个工具
        tool: ToolDto = _service.get_one(id)
        return ApiResponse.ok(tool)

    # 获取所有工具
    tools: list[ToolDto] = _service.get_list()
    return ApiResponse.ok(tools)


@router.post("")
async def create_tool(request: dict):
    """创建工具"""
    # 校验工具名称是否为系统内置工具
    tool_name = request.get("name", "")
    if tool_name:
        _check_tool_name(tool_name)

    data = _service.create_one(request)
    _logger.info(f"[tool_create] id={data.id if data else None}")
    return ApiResponse.ok(data)



@router.put("")
async def update_tool(id: int = Query(..., description="Tool ID"), request: dict = None):
    """更新工具"""
    # 校验工具名称是否为系统内置工具
    tool_name = request.get("name", "") if request else ""
    if tool_name:
        _check_tool_name(tool_name)

    data = _service.update(id, request or {})
    _logger.info(f"[tool_update] id={id}")
    return ApiResponse.ok(data)



@router.delete("")
async def delete_tool(id: int = Query(..., description="Tool ID")):
    """删除工具"""
    success = _service.delete_by_id(id)
    return ApiResponse.ok(success)


@router.post("/import")
async def import_tools(request: dict):
    """批量导入工具"""
    tools = request.get("tools", [])
    data = _service.import_tools(tools)
    return ApiResponse.ok(data)


@router.get("/export")
async def export_tools():
    """导出所有工具"""
    tools: list[ToolDto] = _service.export_tools()
    return ApiResponse.ok(tools)


@router.get("/inheritable")
async def get_inheritable_tools():
    """获取可继承的工具列表"""
    from src.modules.tools.dtos import ToolInheritableDto
    tools: list[ToolInheritableDto] = _service.get_inheritable_tools()
    return ApiResponse.ok(tools)


@router.put("/active")
async def toggle_tool_active(
    id: int = Query(..., description="Tool ID"),
    request: dict = None
):
    """切换工具启用状态"""
    is_active = request.get("is_active", True) if request else True
    data = _service.toggle_active(id, is_active)
    return ApiResponse.ok(data)


@router.post("/execute")
async def execute_tool(
    id: int = Query(..., description="Tool ID"),
    request: dict = None
):
    """执行工具"""
    from src.tools.registry import get_registry

    params = request.get("params", {}) if request else {}

    # 1. 调用 service.get_one 获取工具定义
    tool_data: ToolDto = _service.get_one(id)
    if not tool_data:
        raise ValidException("tool is not found")

    # 检查是否启用
    if not tool_data.is_active:
        raise ValidException("tool is not active")

    config = get_app_config()
    metadata = config.get_system_metadata_dict()
    # 2. 组装 JavaScript 脚本
    context, script = wrap_javascript_code(tool_data.code, params, metadata, tool_data.inherit_from)

    # 3. 调用 quickjs_tool 执行拼接的脚本
    registry = get_registry()
    start_time = time.time()

    _logger.info(f"[tool_execute] tool={tool_data.name} script={script} ")

    try:
        result = registry.execute("quickjs", code=script, context=context)
    except Exception as e:
        _logger.error(f"[tool_execute_error] tool={tool_data.name}, error={str(e)}")
        raise ApiException(f"执行失败: {str(e)}")

    # 4. 返回最终结果
    try:
        result_data = json.loads(result)
        return ApiResponse.ok({
            "result": result_data.get("result", result),
            "execution_time": f"{(time.time() - start_time):.3f}s"
        })
    except (json.JSONDecodeError, TypeError):
        return ApiResponse.ok({
            "result": result,
            "execution_time": f"{(time.time() - start_time):.3f}s"
        })


async def _execute_tool_stream(id: int, params: dict, user_info: dict = None) -> None:
    """执行工具并流式发送日志和结果。

    Args:
        id: 工具 ID
        params: 执行参数
        user_info: 用户信息
    """
    from src.tools.registry import get_registry

    try:
        # 1. 获取工具定义
        tool_data: ToolDto = _service.get_one(id)
        if not tool_data:
            send_queue({
                "type": "error",
                "message": "工具不存在"
            }, "error")
            return

        if not tool_data.is_active:
            send_queue({
                "type": "error",
                "message": "工具未启用"
            }, "error")
            return

        send_queue({
            "type": "status",
            "message": f"开始执行工具: {tool_data.name}",
            "tool_name": tool_data.name
        }, "status")

        config = get_app_config()
        metadata = config.get_system_metadata_dict()
        # 2. 组装 JavaScript 脚本

        # 3. 调用 quickjs_tool 执行脚本
        registry = get_registry()
        _logger.info(f"[tool_execute_stream] tool={tool_data.name}")

        try:
            tool = registry.get("quickjs")
            context, script = wrap_javascript_code(tool_data.code, params, metadata, tool_data.inherit_from)
            # 发送开始执行信号
            send_queue({
                "type": "start",
                "tool_name": tool_data.name,
                "script": script[:500] + "..." if len(script) > 500 else script
            }, "start")
            # 使用异步方法执行工具，context 会在内部自动暴露和释放
            result = await registry.aexecute("quickjs", code=script, tool_name=tool_data.name, context=context)

            # 解析结果
            try:
                result_data = json.loads(result)
                result_value = result_data.get("result", result)
            except (json.JSONDecodeError, TypeError):
                result_value = result

            # 发送完成信号
            send_queue({
                "type": "done",
                "tool_name": tool_data.name,
                "result": result_value,
                "execution_time": 0  # 简化，不计算精确时间
            }, "done")

        except Exception as e:
            _logger.error(f"[tool_execute_stream_error] tool={tool_data.name}, error={str(e)}")
            send_queue({
                "type": "error",
                "tool_name": tool_data.name,
                "message": f"执行失败: {str(e)}"
            }, "error")

    except Exception as e:
        _logger.error(f"[tool_execute_stream_error] unexpected error: {str(e)}")
        send_queue({
            "type": "error",
            "message": f"内部错误: {str(e)}"
        }, "error")


@router.post("/execute/stream")
async def execute_tool_stream(
    id: int = Query(..., description="Tool ID"),
    request: dict = None
):
    """执行工具并通过 SSE 流式返回日志和结果。

    支持实时推送 console.log/warn/error 输出到前端。
    """
    params = request.get("params", {}) if request else {}
    user_info = request.get("user_info", {}) if request else {}

    # 创建异步任务
    queue = create_queue_task(_execute_tool_stream, id, params, user_info)

    async def generate_stream() -> AsyncGenerator[str, None]:
        """从队列中读取数据并生成 SSE 事件。"""
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream; charset=utf-8"
    )
