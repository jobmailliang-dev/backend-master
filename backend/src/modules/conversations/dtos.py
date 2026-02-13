"""对话和消息数据传输对象（DTO）"""

from typing import List
from pydantic import BaseModel, Field


class ConversationDto(BaseModel):
    """对话数据传输对象"""
    id: str = Field(..., description="对话唯一标识")
    title: str = Field(default="新对话", description="对话标题")
    preview: str = Field(default="", description="最新消息预览")
    createTime: int = Field(..., description="创建时间戳")
    updateTime: int = Field(..., description="更新时间戳")
    messageCount: int = Field(default=0, description="消息数量")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conv_abc123",
                "title": "新对话",
                "preview": "你好",
                "createTime": 1704067200000,
                "updateTime": 1704067200000,
                "messageCount": 2
            }
        }


class ConversationListDto(BaseModel):
    """对话列表数据传输对象"""
    data: List[ConversationDto] = Field(default_factory=list, description="对话列表")


class MessageDto(BaseModel):
    """消息数据传输对象"""
    id: str = Field(..., description="消息唯一标识")
    conversationId: str = Field(..., description="所属对话ID")
    role: str = Field(..., description="角色（user/assistant）")
    content: str = Field(..., description="消息内容")
    timestamp: int = Field(..., description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_xyz789",
                "conversationId": "conv_abc123",
                "role": "user",
                "content": "你好",
                "timestamp": 1704067200000
            }
        }


class MessageListDto(BaseModel):
    """消息列表数据传输对象"""
    conversationId: str = Field(..., description="对话ID")
    messages: List[MessageDto] = Field(default_factory=list, description="消息列表")
