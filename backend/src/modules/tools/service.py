"""工具服务层

提供工具的 CRUD 操作和业务逻辑。
使用 IService[ToolDto] 接口约束数据类型。
"""

from typing import List, Optional, Dict, Any
import json
from injector import inject
from .models import Tool, ToolParameter
from .dao import ToolDao
from .dtos import ToolDto, ToolInheritableDto
from src.modules.base import IService, ValidException
from src.utils.logger import get_logger
from src.tools.registry import get_registry
from src.tools.base import BaseTool

logger = get_logger(__name__)


class IToolService(IService[ToolDto]):
    """工具服务接口

    继承 IService[ToolDto]，约束返回数据类型为 ToolDto。
    可扩展工具特有的方法签名。
    """

    def toggle_active(self, tool_id: int, is_active: bool) -> ToolDto:
        """切换工具启用状态"""
        ...

    def import_tools(self, tools_data: List[dict]) -> List[ToolDto]:
        """批量导入工具"""
        ...

    def export_tools(self) -> List[ToolDto]:
        """导出所有工具"""
        ...

    def get_inheritable_tools(self) -> List[ToolInheritableDto]:
        """获取可继承的工具列表"""
        ...


class ToolService(IToolService):
    """工具服务实现

    实现 IToolService 接口，约束返回数据类型为 ToolDto。
    所有校验异常抛出 ValidException。
    """

    @inject
    def __init__(self, dao: ToolDao):
        """初始化服务

        Args:
            dao: 工具数据访问对象
        """
        self._dao = dao

    # --- IToolService 扩展方法 ---

    def get_list(self) -> List[ToolDto]:
        """获取所有工具"""
        return [self.convert_dto(tool) for tool in self._dao.get_all()]

    def get_one(self, tool_id: int) -> Optional[ToolDto]:
        """获取单个工具"""
        tool = self._dao.get_by_id(tool_id)
        return self.convert_dto(tool) if tool else None

    def toggle_active(self, tool_id: int, is_active: bool) -> ToolDto:
        """切换工具启用状态"""
        tool = self._dao.get_by_id(tool_id)
        if not tool:
            raise ValidException("Tool not found", "id")

        tool.is_active = is_active
        self._dao.update(tool)

        # 重新加载工具到注册表
        self.reload_tool(tool_id, flush=True)

        return  self.convert_dto(tool)

    def import_tools(self, tools_data: List[dict]) -> List[ToolDto]:
        """批量导入工具"""
        imported = []
        errors = []

        for tool_data in tools_data:
            if not tool_data.get("name"):
                errors.append("工具缺少名称")
                continue

            existing = self._dao.get_by_name(tool_data["name"])

            if existing:
                result = self.update(existing.id, tool_data)
                if result:
                    imported.append(self.convert_dto(result))
                else:
                    errors.append(f"更新 '{tool_data['name']}' 失败")
            else:
                try:
                    result = self.create_one(tool_data)
                    imported.append(result)
                except ValidException as e:
                    errors.append(f"创建 '{tool_data['name']}' 失败: {e.message}")

        return imported

    def export_tools(self) -> List[ToolDto]:
        """导出所有工具"""
        return [self.convert_dto(tool) for tool in self._dao.get_all()]

    def get_inheritable_tools(self) -> List[ToolInheritableDto]:
        """获取可继承的工具列表

        从注册表中获取所有已注册的工具（包括内置工具和动态工具），
        并转换为 ToolInheritableDto 格式。
        """
        registry = get_registry()
        dto_list: List[ToolInheritableDto] = []

        # 遍历注册表中的所有工具
        for tool_name in registry.list_all():
            tool = registry.get(tool_name)
            if tool is None:
                continue

            # 构建参数列表
            parameters = self._convert_parameters(tool.get_parameters())

            dto_list.append(
                ToolInheritableDto(
                    name=tool.name,
                    description=tool.description,
                    parameters=parameters
                )
            )

        return dto_list

    def _convert_parameters(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将 JSON Schema 格式的参数转换为 DTO 格式

        Args:
            schema: JSON Schema 格式的参数定义

        Returns:
            DTO 格式的参数列表
        """
        parameters: List[Dict[str, Any]] = []

        if not schema:
            return parameters

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name, prop in properties.items():
            param: Dict[str, Any] = {
                "name": name,
                "description": prop.get("description", ""),
                "type": prop.get("type", "any"),
                "required": name in required
            }

            # 空值处理
            if "default" in prop:
                param["default"] = prop["default"]
            if "enum" in prop:
                param["enum"] = prop["enum"]

            parameters.append(param)

        return parameters

    def convert_dto(self, entity) -> ToolDto:
        """将实体转换为 DTO

        Args:
            entity: 实体对象或字典

        Returns:
            ToolDto: DTO 对象
        """
        if isinstance(entity, Tool):
            data = entity.to_dict()
        else:
            data = entity

        return ToolDto(
            id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
            parameters=data.get("parameters", []),
            inherit_from=data.get("inherit_from"),
            code=data.get("code", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


    def create_one(self, data: dict) -> ToolDto:
        """创建工具实体

        Args:
            data: 工具数据字典

        Returns:
            Tool: 创建的工具实体

        Raises:
            ValidException: 校验失败时抛出
        """
        # 校验必填字段
        if not data.get("name"):
            raise ValidException("工具名称不能为空", "name")
        if not data.get("description"):
            raise ValidException("工具描述不能为空", "description")

        # 检查名称是否已存在
        if self._dao.get_by_name(data["name"]):
            raise ValidException(f"工具名称 '{data['name']}' 已存在", "name")

        # 构建工具对象
        tool = Tool(
            name=data["name"],
            description=data["description"],
            is_active=data.get("is_active", True),
            parameters_json=json.dumps(data.get("parameters", [])),
            inherit_from=data.get("inherit_from"),
            code=data.get("code", "")
        )

        tool_id = self._dao.create(tool)
        tool.id = tool_id

        # 重新加载工具到注册表
        self.reload_tool(tool_id, flush=True)

        return self.convert_dto(tool)

    def update(self, tool_id: int, data: dict) -> Optional[Tool]:
        """更新工具实体

        Args:
            tool_id: 工具 ID
            data: 更新数据字典

        Returns:
            Tool: 更新后的工具实体，未找到返回 None

        Raises:
            ValidException: 校验失败时抛出
        """
        tool = self._dao.get_by_id(tool_id)
        if not tool:
            raise ValidException("Tool not found", "id")

        # 更新字段
        if "name" in data:
            existing = self._dao.get_by_name(data["name"])
            if existing and existing.id != tool_id:
                raise ValidException(f"工具名称 '{data['name']}' 已存在", "name")
            tool.name = data["name"]

        if "description" in data:
            tool.description = data["description"]

        if "is_active" in data:
            tool.is_active = data["is_active"]

        if "parameters" in data:
            tool.parameters_json = json.dumps(data["parameters"])

        if "inherit_from" in data:
            tool.inherit_from = data["inherit_from"]

        if "code" in data:
            tool.code = data["code"]

        self._dao.update(tool)

        # 重新加载工具到注册表
        self.reload_tool(tool_id, flush=True)

        return tool

    def delete_by_id(self, tool_id: int) -> bool:
        """删除工具

        Args:
            tool_id: 工具 ID

        Returns:
            bool: 删除成功返回 True

        Raises:
            ValidException: 工具不存在时抛出
        """
        tool = self._dao.get_by_id(tool_id)
        if not tool:
            raise ValidException("Tool not found", "id")

        self._dao.delete(tool_id)

        # 从注册表移除工具
        self.reload_tool(tool_id, flush=False)

        return True

    def reload_tool(self, tool_id: int, flush: bool = False) -> None:
        """重新加载工具到注册表

        Args:
            tool_id: 工具 ID
            flush: 是否重新加载工具，默认为 False
                   - False: 只移除工具
                   - True: 移除工具后再重新注册
        """
        from src.tools.registry import remove_tool, register_tool
        from src.tools.builtins import DynamicTool

        # 获取工具信息
        tool = self._dao.get_by_id(tool_id)
        if not tool:
            return

        # 移除工具
        remove_tool(tool.name)

        # flush=True 时重新注册
        if flush and tool.is_active:
            dynamic_tool = DynamicTool(tool)
            try:
                register_tool(dynamic_tool)
            except ValueError as e:
                # 工具已存在（可能是内置工具）则跳过
                logger.warning(f"[WARN] Skip reload tool '{tool.name}': {e}")


__all__ = ["IToolService", "ToolService", "ToolDto", "ToolInheritableDto"]
