"""工具数据传输对象（DTO）"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ToolDto(BaseModel):
    """工具数据传输对象

    用于 API 接口返回，包含前端展示所需的所有字段。
    """
    id: int = Field(..., description="工具 ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    is_active: bool = Field(default=True, description="是否启用")
    parameters: List[Any] = Field(default_factory=list, description="参数列表")
    inherit_from: Optional[str] = Field(default=None, description="继承自")
    code: str = Field(default="", description="工具代码")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "bash",
                "description": "Execute bash commands",
                "is_active": True,
                "parameters": [
                    {"name": "cmd", "description": "Command to execute", "type": "string", "required": True}
                ],
                "inherit_from": None,
                "code": "",
                "created_at": "2026-01-01 00:00:00",
                "updated_at": "2026-01-01 00:00:00"
            }
        }


class ToolListDto(BaseModel):
    """工具列表数据传输对象"""
    data: List[ToolDto] = Field(default_factory=list, description="工具列表")
    total: int = Field(default=0, description="总数")


class ToolInheritableDto(BaseModel):
    """可继承工具数据传输对象（精简版）"""
    id: int = Field(..., description="工具 ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: List[Any] = Field(default_factory=list, description="参数列表")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "bash",
                "description": "Execute bash commands",
                "parameters": [
                    {"name": "cmd", "description": "Command to execute", "type": "string", "required": True}
                ]
            }
        }


class ToolExecuteResultDto(BaseModel):
    """工具执行结果数据传输对象"""
    result: Any = Field(..., description="执行结果")
    execution_time: str = Field(..., description="执行时间")
