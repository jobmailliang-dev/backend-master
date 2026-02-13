"""对话和消息 API 路由"""

from typing import Optional
from fastapi import APIRouter, Query
from src.api.models import ApiResponse
from src.modules import ConversationService, MessageService, get_injector

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
_injector = get_injector()


def get_conversation_service() -> ConversationService:
    """获取 ConversationService 实例"""
    return _injector.get(ConversationService)


def get_message_service() -> MessageService:
    """获取 MessageService 实例"""
    return _injector.get(MessageService)


@router.get("")
async def get_conversations():
    """获取对话列表（按更新时间倒序）"""
    service = get_conversation_service()
    return ApiResponse.ok(service.get_list())


@router.post("")
async def create_conversation(title: str = Query(default="新对话")):
    """创建新对话"""
    service = get_conversation_service()
    conv = service.create_title(title)
    return ApiResponse.ok(conv)


@router.delete("")
async def delete_conversation(id: str = Query(..., description="对话ID")):
    """删除对话"""
    service = get_conversation_service()
    success = service.delete_by_str_id(id)
    return ApiResponse.ok({"success": success})


@router.patch("")
async def update_conversation(
    id: str = Query(..., description="对话ID"),
    title: Optional[str] = Query(default=None, description="新标题"),
    preview: Optional[str] = Query(default=None, description="新预览")
):
    """更新对话"""
    service = get_conversation_service()
    data = {}
    if title is not None:
        data["title"] = title
    if preview is not None:
        data["preview"] = preview

    if not data:
        return ApiResponse.fail("没有需要更新的字段")

    conv = service.update_by_id(id, data)
    if not conv:
        return ApiResponse.fail("对话不存在")

    return ApiResponse.ok(service.convert_dto(conv))


@router.get("/messages")
async def get_messages(conversationId: str = Query(..., description="对话ID")):
    """获取指定对话的消息列表"""
    service = get_message_service()
    messages = service.get_by_conversation_id(conversationId)
    return ApiResponse.ok({
        "conversationId": conversationId,
        "messages": [msg.dict() for msg in messages]
    })


@router.post("/messages")
async def create_message(
    conversationId: str = Query(..., description="对话ID"),
    role: str = Query(..., description="角色（user/assistant）"),
    content: str = Query(..., description="消息内容")
):
    """创建消息"""
    service = get_message_service()
    message = service.create_message(conversationId, role, content)
    return ApiResponse.ok(message)
