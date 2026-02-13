"""对话和消息服务层

提供对话和消息的 CRUD 操作和业务逻辑。
"""

import time
import uuid
from typing import List, Optional
from injector import inject
from .models import Conversation, Message
from .dao import ConversationDao, MessageDao
from .dtos import ConversationDto, MessageDto
from src.modules.base import IService, ValidException


def generate_id() -> str:
    """生成唯一ID"""
    now = time.time()
    now_str = str(int(now * 1000))
    rand = uuid.uuid4().hex[:6]
    return f"conv_{now_str}_{rand}"


def generate_message_id() -> str:
    """生成消息唯一ID"""
    now = time.time()
    now_str = str(int(now * 1000))
    rand = uuid.uuid4().hex[:6]
    return f"msg_{now_str}_{rand}"


class IConversationService(IService[ConversationDto]):
    """对话服务接口"""

    def get_by_id(self, conversation_id: str) -> Optional[ConversationDto]:
        """根据ID获取对话"""
        ...

    def create_one(self, title: str = "新对话") -> ConversationDto:
        """创建对话"""
        ...

    def update_title(self, conversation_id: str, title: str) -> Optional[ConversationDto]:
        """更新对话标题"""
        ...

    def update_preview(self, conversation_id: str, preview: str) -> Optional[ConversationDto]:
        """更新对话预览"""
        ...

    def delete_by_id(self, conversation_id: str) -> bool:
        """删除对话"""
        ...


class IMessageService(IService[MessageDto]):
    """消息服务接口"""

    def get_by_conversation_id(self, conversation_id: str) -> List[MessageDto]:
        """获取对话的所有消息"""
        ...

    def create_message(
        self, conversation_id: str, role: str, content: str
    ) -> MessageDto:
        """创建消息"""
        ...


class ConversationService(IConversationService):
    """对话服务实现"""

    @inject
    def __init__(self, dao: ConversationDao, message_dao: MessageDao):
        self._dao = dao
        self._message_dao = message_dao

    def get_list(self) -> List[ConversationDto]:
        """获取所有对话"""
        return [self.convert_dto(conv) for conv in self._dao.get_all()]

    def get_one(self, conversation_id: int) -> Optional[ConversationDto]:
        """获取单个对话（接口兼容）"""
        return self.get_by_id(str(conversation_id))

    def get_by_id(self, conversation_id: str) -> Optional[ConversationDto]:
        """根据ID获取对话"""
        conv = self._dao.get_by_id(conversation_id)
        return self.convert_dto(conv) if conv else None

    def create_one(self, data: dict = None) -> ConversationDto:
        """创建对话"""
        title = "新对话"
        if data and data.get("title"):
            title = data["title"]

        now = int(time.time() * 1000)
        conversation = Conversation(
            id=generate_id(),
            title=title,
            preview="",
            create_time=now,
            update_time=now,
            message_count=0
        )
        self._dao.create(conversation)
        return self.convert_dto(conversation)

    def create_title(self, title: str = "新对话") -> ConversationDto:
        """创建对话（兼容接口）"""
        return self.create_one({"title": title})

    def update(self, conversation_id: int, data: dict) -> Optional[Conversation]:
        """更新对话（接口兼容）"""
        return self.update_by_id(str(conversation_id), data)

    def update_by_id(self, conversation_id: str, data: dict) -> Optional[Conversation]:
        """根据ID更新对话"""
        conv = self._dao.get_by_id(conversation_id)
        if not conv:
            return None

        if "title" in data:
            conv.title = data["title"]
        if "preview" in data:
            conv.preview = data["preview"]
        if "messageCount" in data:
            conv.message_count = data["messageCount"]

        conv.update_time = int(time.time() * 1000)
        self._dao.update(conv)
        return conv

    def update_title(self, conversation_id: str, title: str) -> Optional[ConversationDto]:
        """更新对话标题"""
        conv = self.update_by_id(conversation_id, {"title": title})
        return self.convert_dto(conv) if conv else None

    def update_preview(self, conversation_id: str, preview: str) -> Optional[ConversationDto]:
        """更新对话预览"""
        conv = self.update_by_id(conversation_id, {"preview": preview})
        return self.convert_dto(conv) if conv else None

    def delete_by_id(self, conversation_id: int) -> bool:
        """删除对话（接口兼容）"""
        return self.delete_by_str_id(str(conversation_id))

    def delete_by_str_id(self, conversation_id: str) -> bool:
        """根据ID删除对话"""
        # 先删除该对话的所有消息
        self._message_dao.delete_by_conversation_id(conversation_id)
        return self._dao.delete(conversation_id)

    def convert_dto(self, entity) -> ConversationDto:
        """将实体转换为 DTO"""
        if isinstance(entity, Conversation):
            data = entity.to_dict()
        else:
            data = entity

        return ConversationDto(
            id=data.get("id", ""),
            title=data.get("title", "新对话"),
            preview=data.get("preview", ""),
            createTime=data.get("createTime", data.get("create_time", 0)),
            updateTime=data.get("updateTime", data.get("update_time", 0)),
            messageCount=data.get("messageCount", data.get("message_count", 0))
        )


class MessageService(IMessageService):
    """消息服务实现"""

    @inject
    def __init__(self, dao: MessageDao, conversation_dao: ConversationDao):
        self._dao = dao
        self._conversation_dao = conversation_dao

    def get_list(self) -> List[MessageDto]:
        """获取所有消息（接口兼容）"""
        return []

    def get_one(self, message_id: int) -> Optional[MessageDto]:
        """获取单个消息（接口兼容）"""
        return None

    def get_by_conversation_id(self, conversation_id: str) -> List[MessageDto]:
        """获取对话的所有消息"""
        messages = self._dao.get_by_conversation_id(conversation_id)
        return [self.convert_dto(msg) for msg in messages]

    def create_one(self, data: dict) -> MessageDto:
        """创建消息"""
        conversation_id = data.get("conversation_id", "")
        role = data.get("role", "user")
        content = data.get("content", "")

        if not conversation_id:
            raise ValidException("conversation_id 不能为空", "conversation_id")

        return self.create_message(conversation_id, role, content)

    def create_message(
        self, conversation_id: str, role: str, content: str
    ) -> MessageDto:
        """创建消息并更新对话"""
        now = int(time.time() * 1000)

        message = Message(
            id=generate_message_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=now
        )
        self._dao.create(message)

        # 更新对话的 message_count 和 preview
        conv = self._conversation_dao.get_by_id(conversation_id)
        if conv:
            message_count = self._dao.count_by_conversation_id(conversation_id)
            preview = content[:50] if content else ""
            if role == "assistant":
                preview = content[:50] if content else ""

            self._conversation_dao.update(Conversation(
                id=conversation_id,
                title=conv.title,
                preview=preview,
                create_time=conv.create_time,
                update_time=now,
                message_count=message_count
            ))

        return self.convert_dto(message)

    def update(self, message_id: int, data: dict) -> Optional[Message]:
        """更新消息（接口兼容）"""
        return None

    def delete_by_id(self, message_id: int) -> bool:
        """删除消息（接口兼容）"""
        return False

    def convert_dto(self, entity) -> MessageDto:
        """将实体转换为 DTO"""
        if isinstance(entity, Message):
            data = entity.to_dict()
        else:
            data = entity

        return MessageDto(
            id=data.get("id", ""),
            conversationId=data.get("conversationId", data.get("conversation_id", "")),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", 0)
        )


__all__ = [
    "IConversationService",
    "ConversationService",
    "IMessageService",
    "MessageService",
    "ConversationDto",
    "MessageDto"
]
