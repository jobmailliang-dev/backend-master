[根目录](../../CLAUDE.md) > [llm-cli-v3](../) > **data/skills**

# Skills 模块

## 模块职责

Skills 模块是 LLM CLI V3 的技能数据目录，提供领域特定的预定义上下文内容。技能以 Markdown 格式存储，支持 YAML frontmatter 定义元数据，可被 LLM 在对话中动态加载和调用。

每个技能代表一个特定领域的知识或操作指南，如 PDF 处理、订单管理、工作站信息等。

## 入口与启动

### 技能目录结构

```
data/skills/
  SKILL.md           # 技能定义（YAML frontmatter + 内容）
  *.md               # 相关文档

技能类型/
  SKILL.md           # 技能主文件
  *.md               # 辅助文档
  scripts/           # Python 脚本（如有）
```

### 技能加载器

技能通过 `backend/src/skills/loader.py` 中的 `SkillLoader` 类加载：

```python
class SkillLoader:
    def load(self, skill_name: str) -> Skill: ...
    def list_skill_names(self) -> List[str]: ...
```

### 技能执行器

技能通过 `backend/src/skills/executor.py` 中的 `SkillExecutor` 类执行：

```python
class SkillExecutor:
    def execute(self, skill_name: str, args: Dict[str, Any] = None) -> str: ...
    def list_available_skills(self) -> List[str]: ...
```

## 对外接口

### 技能工具调用

技能通过 `skill` 工具加载：

```json
{
  "tool_calls": [{
    "function": {
      "name": "skill",
      "arguments": "{\"skill_name\": \"pdf\"}"
    }
  }]
}
```

### 技能定义格式

```yaml
---
name: skill_name
description: 技能描述，供 LLM 理解何时使用
license: 许可证类型（可选）
---

# 技能内容

支持 Markdown 格式，包含代码示例、操作指南等。

支持占位符替换：{param_name}
```

### 技能元数据

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 技能名称，唯一标识 |
| description | string | 技能描述 |
| license | string | 许可证（可选） |
| allowed_tools | list | 允许的工具列表（可选） |

## 当前技能列表

### 1. my-skill

```
data/skills/my-skill/
  SKILL.md           # 示例技能
```

**职责**: 提供示例技能模板，展示技能的基本结构和用法

### 2. order

```
data/skills/order/
  SKILL.md                   # 订单技能
  order_progress_deviation.md # 订单进度偏差处理
```

**职责**: 提供订单管理和进度偏差处理相关的知识和指南

### 3. pdf

```
data/skills/pdf/
  SKILL.md                   # PDF 处理主技能
  forms.md                   # PDF 表单处理指南
  reference.md               # 参考资料
  LICENSE.txt                # 许可证
  scripts/                   # Python 脚本工具
    extract_form_field_info.py
    fill_fillable_fields.py
    fill_pdf_form_with_annotations.py
    check_bounding_boxes.py
    check_bounding_boxes_test.py  # 唯一测试文件
    check_fillable_fields.py
    convert_pdf_to_images.py
    create_validation_image.py
```

**职责**: 提供全面的 PDF 处理能力，包括：

- 文本和表格提取（pypdf, pdfplumber）
- PDF 创建（reportlab）
- PDF 合并/拆分（pypdf）
- 表单填充（pdf-lib, pypdf）
- 格式转换

### 4. workstation

```
data/skills/workstation/
  SKILL.md             # 工作站技能
  workstation_list.md  # 工作站列表信息
```

**职责**: 提供工作站相关的信息和管理指南

## 关键依赖与配置

### Python 库（PDF 技能依赖）

| 库 | 用途 |
|------|------|
| pypdf | PDF 读写、合并、拆分 |
| pdfplumber | 文本和表格提取 |
| reportlab | PDF 创建 |
| pdf-lib | JavaScript PDF 操作 |
| pytesseract | OCR 支持 |

### 技能系统配置

技能通过 `config.yaml` 中的 `tools.allowed_tools` 控制可用性：

```yaml
tools:
  allowed_tools:
    - skill
    # 其他工具...
```

## 测试与质量

### 测试覆盖

- **当前状态**: 测试覆盖极低
- **已有测试**: 仅 `pdf/scripts/check_bounding_boxes_test.py`
- **建议**: 为 skills/executor.py、loader.py 补充单元测试

### 技能质量检查清单

- [ ] SKILL.md 包含完整的 YAML frontmatter
- [ ] 技能描述清晰，能帮助 LLM 判断使用场景
- [ ] 包含代码示例和使用场景
- [ ] 辅助文档（如有）组织良好

## 常见问题 (FAQ)

**Q: 如何创建新技能？**

1. 在 `data/skills/` 创建新目录
2. 添加 `SKILL.md` 文件
3. 使用 YAML frontmatter 定义元数据
4. 编写技能内容（Markdown 格式）
5. 可选：添加辅助文档和脚本

**Q: 技能如何使用占位符？**

在技能内容中使用 `{param_name}` 格式的占位符，调用时通过参数替换：

```yaml
---
name: example
description: 示例技能
---

执行操作：{action_name}
目标：{target}
```

**Q: 如何为技能添加脚本？**

在技能目录下创建 `scripts/` 目录，添加 Python 脚本：

```
data/skills/pdf/scripts/
  convert_pdf_to_images.py
```

**Q: 技能如何控制可用工具？**

在 SKILL.md frontmatter 中添加 `allowed_tools` 字段：

```yaml
---
name: pdf
description: PDF 处理技能
allowed_tools:
  - read_file
  - bash
```

## 相关文件清单

### 核心文件

| 文件 | 职责 |
|------|------|
| `backend/src/skills/executor.py` | 技能执行器 |
| `backend/src/skills/loader.py` | 技能加载器 |
| `backend/src/skills/parser.py` | 技能解析器 |
| `backend/src/tools/builtins/skill_tool.py` | 技能工具实现 |

### 技能文件

| 文件 | 描述 |
|------|------|
| `data/skills/my-skill/SKILL.md` | 示例技能 |
| `data/skills/order/SKILL.md` | 订单管理技能 |
| `data/skills/pdf/SKILL.md` | PDF 处理技能 |
| `data/skills/workstation/SKILL.md` | 工作站技能 |

## 变更记录 (Changelog)

| 时间戳 | 操作 | 说明 |
|--------|------|------|
| 2026-02-03 11:32:16 | 初始化 | 首次生成模块 AI 上下文文档 |
