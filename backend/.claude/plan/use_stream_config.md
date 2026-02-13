# 规划文档：use_stream 配置参数与 complete_auto 方法

## 1. 需求概述

为 `config.yaml` 中的 `openai` 节点新增 `use_stream` 参数（默认 `false`），在 `OpenAIClientAdapter` 中定义 `complete_auto` 方法，根据配置自适应选择流式或非流式调用，兼容更多模型特性。

## 2. 方案分析

### 2.1 方案一：用户原方案（添加 complete_auto 方法）

**实现方式：**
- `complete_auto` 方法内部判断 `use_stream` 配置，调用 `complete` 或 `complete_stream`

**优点：**
- 改动集中，不影响现有 `complete`/`complete_stream` 方法
- 清晰分离流式/非流式逻辑

**缺点：**
- `complete_stream` 返回 `Generator`，`complete` 返回 `str/dict`，返回类型不一致
- `client.py` 调用方需要处理两种不同的返回类型
- 如果流式结果需要聚合为统一格式，需要额外处理逻辑

**问题：** `client.py` 中 `self.adapter.complete()` 调用位置（`client.py:71`）需要改为判断返回值类型或聚合流式结果。

### 2.2 方案二：修改 complete_stream 返回统一格式（推荐）

**实现方式：**
- 修改 `complete_stream` 使其始终返回完整响应（聚合所有 chunk），与 `complete` 返回格式一致
- `complete_auto` 只是选择调用方式

**优点：**
- 调用方（`client.py`）无需感知底层是流式还是非流式
- 返回类型统一为 `str` 或 `dict`
- 向后兼容，不破坏现有功能

**缺点：**
- `complete_stream` 语义改变：原来是"流式输出"，现在是"流式获取完整结果"

### 2.3 方案三：添加 use_stream 参数到 complete 方法

**实现方式：**
- 在 `complete` 方法中增加 `stream` 参数
- `complete_auto` 只是简单代理

**优点：**
- API 更简洁，减少方法数量

**缺点：**
- 违反单一职责原则
- `complete` 方法变得复杂

### 2.4 方案对比

| 维度 | 方案一（complete_auto） | 方案二（统一格式） | 方案三（参数控制） |
|------|------------------------|-------------------|-------------------|
| 调用方改动 | 需要处理两种返回类型 | 无需改动 | 无需改动 |
| 代码复杂度 | 中等（需类型判断） | 低 | 低 |
| 向后兼容 | 是 | 是 | 部分（接口膨胀） |
| 职责清晰度 | 高 | 高 | 低 |

## 3. 推荐方案

**推荐方案二**，理由：
- 对调用方完全透明，`client.py` 无需任何改动
- 返回类型统一，便于维护和扩展
- `complete_auto` 方法简单直接

## 4. 实施步骤

### 步骤 1：修改配置模型 (`src/config/models.py`)

```python
@dataclass
class OpenAIConfig:
    api_url: str
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    system_message: str = "You are a helpful assistant."
    use_stream: bool = False  # 新增
```

### 步骤 2：修改配置加载器 (`src/config/loader.py`)

```python
def _parse_openai_config(raw: dict) -> OpenAIConfig:
    return OpenAIConfig(
        api_url=raw.get('api_url', ''),
        api_key=raw.get('api_key', ''),
        model=raw.get('model', 'gpt-3.5-turbo'),
        max_tokens=raw.get('max_tokens', 1000),
        temperature=raw.get('temperature', 0.7),
        system_message=raw.get('system_message', 'You are a helpful assistant.'),
        use_stream=raw.get('use_stream', False),  # 新增
    )
```

### 步骤 3：修改 config.yaml 示例配置

```yaml
openai:
  api_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  model: "gpt-3.5-turbo"
  max_tokens: 1000
  temperature: 0.7
  use_stream: false  # 新增
```

### 步骤 4：修改适配器基类 (`src/adapters/base.py`)

添加 `complete_auto` 抽象方法：

```python
@abstractmethod
def complete_auto(
    self,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]] = None,
    **kwargs,
) -> str:
    """根据配置自动选择流式或非流式调用。

    Returns:
        AI 回复内容（字符串或包含 tool_calls 的字典）
    """
    pass
```

### 步骤 5：修改 OpenAI 适配器 (`src/adapters/openai.py`)

#### 5.1 修改 `__init__` 方法，保存 `use_stream` 配置

```python
def __init__(self, config: OpenAIConfig):
    """初始化适配器。"""
    self.client = OpenAI(
        base_url=config.api_url if config.api_url else None,
        api_key=config.api_key,
    )
    self.model = config.model
    self.max_tokens = config.max_tokens
    self.temperature = config.temperature
    self.use_stream = config.use_stream  # 新增
```

#### 5.2 添加 `complete_auto` 方法（核心改动）

**`complete_stream` 保持不变**，在 `complete_auto` 中完成数据聚合：

```python
def complete_auto(
    self,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]] = None,
    **kwargs,
) -> str:
    """根据配置自动选择流式或非流式调用。

    流式模式下会在内部聚合所有 chunk 后返回统一格式。
    """
    if self.use_stream:
        # 流式调用：聚合所有 chunk 后返回
        full_content = ""
        tool_calls = []

        for chunk in self.complete_stream(messages, tools, **kwargs):
            if chunk.get("content"):
                full_content += chunk["content"]
            if chunk.get("tool_calls"):
                tool_calls.extend(chunk["tool_calls"])

        if tool_calls:
            return {"content": full_content or "", "tool_calls": tool_calls}
        return full_content
    else:
        return self.complete(messages, tools, **kwargs)
```

### 步骤 6：修改客户端 (`src/core/client.py`)

修改 `client.py:71` 处的调用：

```python
# 原代码
response = self.adapter.complete(messages=messages, tools=available_schemas)

# 修改为
response = self.adapter.complete_auto(messages=messages, tools=available_schemas)
```

**注意：** 由于 `complete_stream` 现在返回完整响应（与 `complete` 格式一致），`client.py` 中对 `response` 的处理逻辑无需任何改动。

## 5. 风险与注意事项

1. **配置传递**：确保 `use_stream` 从配置文件正确传递到适配器
2. **工具调用兼容性**：流式模式下的工具调用解析需与非流式保持一致
3. **代码复用**：`complete_stream` 保持 Generator 语义，`complete_auto` 负责聚合

## 6. 验收标准

1. `config.yaml` 支持 `use_stream` 配置项，默认 `false`
2. `use_stream: false` 时，使用原有的非流式调用
3. `use_stream: true` 时，使用流式调用并聚合结果
4. 两种模式的返回结果格式一致，`client.py` 无需区分处理
5. 现有功能（CLI/Web 模式）保持正常工作
