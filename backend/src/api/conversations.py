"""对话和消息 API 路由"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from src.api.models import ApiResponse
from src.modules import ConversationService, MessageService
from src.core import get_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    """创建对话请求体"""
    title: str = "新对话"
    user_id: str = ""


class UpdateConversationRequest(BaseModel):
    """更新对话请求体"""
    id: str
    title: Optional[str] = None
    preview: Optional[str] = None
    messageCount: Optional[int] = None


@router.get("")
async def get_conversations(user_id: str = Query(..., description="用户ID")):
    """获取对话列表（按更新时间倒序）"""
    service = get_service(ConversationService)
    return ApiResponse.ok(service.get_list(user_id))


@router.post("")
async def create_conversation(request: CreateConversationRequest = None):
    """创建新对话"""
    service = get_service(ConversationService)
    title = "新对话"
    user_id = ""
    if request:
        if request.title:
            title = request.title
        if request.user_id:
            user_id = request.user_id
    conv = service.create_one({"title": title, "user_id": user_id})
    return ApiResponse.ok(conv)


@router.delete("")
async def delete_conversation(request: dict = None):
    """删除对话"""
    # 支持请求体或 Query 参数
    conversation_id = None
    if request and "id" in request:
        conversation_id = request.get("id")

    if not conversation_id:
        return ApiResponse.fail("缺少 id 参数")

    service = get_service(ConversationService)
    success = service.delete_by_str_id(conversation_id)
    return ApiResponse.ok({"success": success})


@router.patch("")
async def update_conversation(request: UpdateConversationRequest = None):
    """更新对话"""
    if not request or not request.id:
        return ApiResponse.fail("缺少 id 参数")

    service = get_service(ConversationService)
    data = {}
    if request.title is not None:
        data["title"] = request.title
    if request.preview is not None:
        data["preview"] = request.preview
    if request.messageCount is not None:
        data["messageCount"] = request.messageCount

    if not data:
        return ApiResponse.fail("没有需要更新的字段")

    conv = service.update(request.id, data)
    if not conv:
        return ApiResponse.fail("对话不存在")

    return ApiResponse.ok(service.convert_dto(conv))


@router.get("/messages")
async def get_messages(conversationId: str = Query(..., description="对话ID")):
    """获取指定对话的消息列表"""
    service = get_service(MessageService)
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
    service = get_service(MessageService)
    message = service.create_message(conversationId, role, content)
    return ApiResponse.ok(message)


class UpdateMetadataRequest(BaseModel):
    """更新元数据请求体"""
    conversation_id: str
    form_data: dict
    message_id: Optional[str] = None
    questions: Optional[list] = None


@router.post("/update_metadata")
async def update_metadata(request: UpdateMetadataRequest):
    """更新对话元数据"""
    if not request.conversation_id:
        return ApiResponse.fail("缺少 conversation_id 参数")

    if not request.form_data:
        return ApiResponse.fail("缺少 form_data 参数")

    # 更新对话元数据
    conv_service = get_service(ConversationService)
    conv = conv_service.update_metadata(request.conversation_id, request.form_data)
    if not conv:
        return ApiResponse.fail("对话不存在")

    # 如果提供了 message_id，更新消息状态为 FINISH
    if request.message_id:
        import json
        msg_service = get_service(MessageService)
        # 获取消息
        messages = msg_service.get_by_conversation_id(request.conversation_id)
        target_msg = None
        for msg in messages:
            if msg.id == request.message_id:
                target_msg = msg
                break

        if target_msg:
            # 解析 content，更新 status 为 FINISH
            try:
                content_data = json.loads(target_msg.content)
                content_data["status"] = "FINISH"

                # 解析 questions，赋值 answer
                if content_data.get("questions"):
                    for question in content_data["questions"]:
                        name = question.get("id")   
                        if name and request.form_data and name in request.form_data:
                            question["answer"] = request.form_data[name]


                new_content = json.dumps(content_data, ensure_ascii=False)
                msg_service.update_message_content(request.message_id, new_content)
            except json.JSONDecodeError:
                pass

    return ApiResponse.ok(conv)
