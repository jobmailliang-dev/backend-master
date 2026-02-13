"""技能解析器。

定义技能相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillFrontmatter:
    """技能前端元数据。"""
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    argument_hint: Optional[str] = None
    when_to_use: Optional[str] = None
    version: Optional[str] = None
    model: Optional[str] = None


@dataclass
class Skill:
    """技能定义。"""
    frontmatter: SkillFrontmatter
    content: str
    file_path: str

    @property
    def name(self) -> str:
        """获取技能名称。"""
        return self.frontmatter.name or ""

    @property
    def description(self) -> str:
        """获取技能描述。"""
        return self.frontmatter.description or ""

    @property
    def allowed_tools(self) -> List[str]:
        """获取允许的工具列表。"""
        return self.frontmatter.allowed_tools

    def format_for_prompt(self, args: Dict[str, Any] = None) -> str:
        """格式化技能内容用于提示。

        Args:
            args: 可选的参数，用于替换占位符

        Returns:
            格式化的技能内容
        """
        content = self.content

        if args:
            for key, value in args.items():
                placeholder = "{" + key + "}"
                content = content.replace(placeholder, str(value))

        return content
