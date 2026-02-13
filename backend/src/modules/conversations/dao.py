"""对话和消息数据访问层"""

from typing import List, Optional
from injector import inject
from .models import Conversation, Message
from ..datasource.connection import Connection


class ConversationDao:
    """对话数据访问对象"""

    @inject
    def __init__(self, conn: Connection):
        self._conn = conn
        self.create_table()

    def create_table(self):
        """创建对话表"""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '新对话',
                preview TEXT DEFAULT '',
                create_time INTEGER NOT NULL,
                update_time INTEGER NOT NULL,
                message_count INTEGER DEFAULT 0
            )
        """)

    def create(self, conversation: Conversation) -> str:
        """创建对话"""
        sql = """
            INSERT INTO conversations (id, title, preview, create_time, update_time, message_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self._conn.execute(sql, (
            conversation.id,
            conversation.title,
            conversation.preview,
            conversation.create_time,
            conversation.update_time,
            conversation.message_count
        ))
        return conversation.id

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据 ID 获取对话"""
        row = self._conn.query_one(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        return Conversation.from_row(row) if row else None

    def get_all(self) -> List[Conversation]:
        """获取所有对话（按更新时间倒序）"""
        rows = self._conn.query_all(
            "SELECT * FROM conversations ORDER BY update_time DESC"
        )
        return [Conversation.from_row(row) for row in rows]

    def update(self, conversation: Conversation) -> bool:
        """更新对话"""
        rowcount = self._conn.execute_update_delete("""
            UPDATE conversations
            SET title = ?, preview = ?, update_time = ?, message_count = ?
            WHERE id = ?
        """, (
            conversation.title,
            conversation.preview,
            conversation.update_time,
            conversation.message_count,
            conversation.id
        ))
        return rowcount > 0

    def delete(self, conversation_id: str) -> bool:
        """删除对话"""
        rowcount = self._conn.execute_update_delete(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        return rowcount > 0


class MessageDao:
    """消息数据访问对象"""

    @inject
    def __init__(self, conn: Connection):
        self._conn = conn
        self.create_table()

    def create_table(self):
        """创建消息表"""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
            ON messages(conversation_id)
        """)

    def create(self, message: Message) -> str:
        """创建消息"""
        sql = """
            INSERT INTO messages (id, conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        self._conn.execute(sql, (
            message.id,
            message.conversation_id,
            message.role,
            message.content,
            message.timestamp
        ))
        return message.id

    def get_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """获取对话的所有消息（按时间正序）"""
        rows = self._conn.query_all(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        return [Message.from_row(row) for row in rows]

    def delete_by_conversation_id(self, conversation_id: str) -> int:
        """删除对话的所有消息"""
        rowcount = self._conn.execute_update_delete(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        return rowcount

    def count_by_conversation_id(self, conversation_id: str) -> int:
        """获取对话的消息数量"""
        row = self._conn.query_one(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        return row[0] if row else 0
