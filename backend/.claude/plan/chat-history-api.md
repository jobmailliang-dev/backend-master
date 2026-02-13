# 聊天记录接口设计文档

## 1. 需求概述

根据前端 mock-server.js 实现真实的聊天记录后端接口，支持对话和消息的 CRUD 操作。

### 1.1 接口清单

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/conversations` | GET | 获取对话列表（按更新时间倒序） |
| `/api/conversations` | POST | 创建新对话 |
| `/api/conversations` | DELETE | 删除对话（query.id） |
| `/api/conversations` | PATCH | 更新对话（query.id, query.title） |
| `/api/conversations/messages` | GET | 获取指定对话的消息列表 |

### 1.2 数据结构

#### Conversation（对话）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 对话唯一标识（如 `conv_xxx`） |
| title | string | 对话标题 |
| preview | string | 最新消息预览 |
| createTime | number | 创建时间戳（毫秒） |
| updateTime | number | 更新时间戳（毫秒） |
| messageCount | number | 消息数量 |

#### Message（消息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息唯一标识 |
| conversationId | string | 所属对话 ID |
| role | string | 角色（user / assistant） |
| content | string | 消息内容 |
| timestamp | number | 时间戳（毫秒） |

---

## 2. 技术方案

### 2.1 模块结构

参考现有 `tools` 模块，采用 **DAO → Service → API** 三层架构：

```
src/modules/conversations/
├── __init__.py       # 导出 ConversationService, ConversationDao, MessageService, MessageDao
├── models.py         # 业务实体（Conversation, Message）
├── dtos.py           # 数据传输对象
├── dao.py            # 数据访问层
└── service.py        # 服务层

src/api/conversations.py  # API 路由层
```

### 2.2 数据库设计

使用 SQLite，扩展现有 `data/app.db` 数据库。

#### conversations 表

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '新对话',
    preview TEXT DEFAULT '',
    create_time INTEGER NOT NULL,
    update_time INTEGER NOT NULL,
    message_count INTEGER DEFAULT 0
);
```

#### messages 表

```sql
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
```

---

## 3. 实施步骤

### 步骤 1：创建业务实体层

**文件**: `src/modules/conversations/models.py`

- 定义 `Conversation` dataclass
- 定义 `Message` dataclass
- 实现 `from_row()` 方法

### 步骤 2：创建 DTO 层

**文件**: `src/modules/conversations/dtos.py`

- `ConversationDto`: 对话 DTO
- `ConversationListDto`: 对话列表 DTO
- `MessageDto`: 消息 DTO
- `MessageListDto`: 消息列表 DTO

### 步骤 3：创建 DAO 层

**文件**: `src/modules/conversations/dao.py`

- `ConversationDao`: 对话数据访问
  - `create_table()`: 建表
  - `create()`: 创建对话
  - `get_by_id()`: 获取对话
  - `get_all()`: 获取所有对话（按 update_time 倒序）
  - `update()`: 更新对话
  - `delete()`: 删除对话
  - `update_message_count()`: 更新消息计数

- `MessageDao`: 消息数据访问
  - `create_table()`: 建表
  - `create()`: 创建消息
  - `get_by_conversation_id()`: 获取对话的所有消息
  - `delete_by_conversation_id()`: 删除对话的所有消息

### 步骤 4：创建 Service 层

**文件**: `src/modules/conversations/service.py`

- `IConversationService`: 对话服务接口
- `ConversationService`: 对话服务实现

- `IMessageService`: 消息服务接口
- `MessageService`: 消息服务实现

### 步骤 5：注册模块

**文件**: `src/modules/__init__.py`

- 导入 `Conversation`, `ConversationService`, `ConversationDao`
- 导入 `Message`, `MessageService`, `MessageDao`
- 创建 `ConversationModule` 和 `MessageModule` 类
- 注册到 `injector`

### 步骤 6：创建 API 路由

**文件**: `src/api/conversations.py`

- `GET /api/conversations`: 获取对话列表
- `POST /api/conversations`: 创建对话
- `DELETE /api/conversations`: 删除对话
- `PATCH /api/conversations`: 更新对话
- `GET /api/conversations/messages`: 获取消息列表

### 步骤 7：注册路由

**文件**: `src/__main__.py`

- 导入 `conversations_router`
- `app.include_router(conversations_router)`

---

## 4. 验收标准

1. ✅ GET `/api/conversations` 返回按更新时间倒序的对话列表
2. ✅ POST `/api/conversations` 创建新对话并返回
3. ✅ DELETE `/api/conversations?id=xxx` 删除指定对话
4. ✅ PATCH `/api/conversations?id=xxx&title=xxx` 更新对话标题
5. ✅ GET `/api/conversations/messages?conversationId=xxx` 返回消息列表
6. ✅ 删除对话时级联删除该对话的所有消息
7. ✅ 聊天发送消息时自动创建/更新对话
8. ✅ 接口响应格式符合 `ApiResponse` 规范
