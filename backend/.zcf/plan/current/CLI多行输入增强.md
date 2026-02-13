# CLI 多行输入增强 - 执行计划

## 目标
重构 CLI 输入模块，支持：
- **Ctrl+Enter**：换行
- **Enter**：发送
- **粘贴换行内容**：保持格式

## 方案选择
采用 **prompt_toolkit** 方案，一次性解决跨平台兼容问题。

---

## 执行步骤

### 步骤 1：添加依赖
**文件**: `requirements.txt`

**操作**:
- 添加 `prompt_toolkit>=3.0.0` 依赖

**预期结果**: 依赖清单包含 prompt_toolkit

---

### 步骤 2：创建新的输入模块
**文件**: `src/cli/prompt_input.py`（新建）

**操作**:
1. 创建 `PromptInput` 类，封装 prompt_toolkit 功能
2. 实现 `get_input()` 方法，返回用户输入文本
3. 配置键位绑定：
   - `Ctrl+Enter` → 换行
   - `Enter` → 发送
   - `Ctrl+C` → 退出
4. 配置多行编辑（`multiline=True`）
5. 添加默认提示符样式

**预期结果**: 新模块可直接替换原 `input.py` 的 `get_input()` 接口

**核心代码结构**:
```python
class PromptInput:
    def __init__(self, prompt: str = ""): ...
    def get_input(self) -> str: ...
```

---

### 步骤 3：创建向后兼容层
**文件**: `src/cli/input.py`

**操作**:
- 重写 `get_input()` 函数，内部委托 `PromptInput` 类
- 保留 `is_exit_command()` 和 `is_empty()` 工具函数
- 移除平台相关的 `_get_input_windows()` 和 `_get_input_unix()`

**预期结果**: `interface.py` 调用方式完全不变

---

### 步骤 4：更新接口欢迎信息
**文件**: `src/cli/interface.py`

**操作**:
- 更新 `print_welcome()` 中的提示文案

**预期结果**: 提示信息准确反映新功能

---

### 步骤 5：测试验证
**操作**:
1. CLI 模式启动：`python -m src --cli`
2. 验证 Ctrl+Enter 换行功能
3. 验证 Enter 发送功能
4. 验证 Ctrl+V 粘贴多行内容
5. 验证 Ctrl+C 退出

**预期结果**: 所有功能正常工作

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `requirements.txt` | 修改 | 添加 prompt_toolkit 依赖 |
| `src/cli/prompt_input.py` | 新建 | prompt_toolkit 封装层 |
| `src/cli/input.py` | 修改 | 保留接口，内部重构 |
| `src/cli/interface.py` | 修改 | 更新提示文案 |

---

## 兼容性说明

| 平台 | 测试优先级 | 预期行为 |
|------|------------|----------|
| Windows | P0 | 完整支持 |
| macOS | P0 | 完整支持 |
| Linux | P0 | 完整支持 |

---

## 回滚计划

如 prompt_toolkit 方案失败，可回滚到 `msvcrt` + `tty` 原方案：
1. 保留 `input.py.bak` 备份
2. 恢复原实现
