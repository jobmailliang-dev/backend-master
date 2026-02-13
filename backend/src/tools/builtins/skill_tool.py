"""技能工具。

执行 Markdown 文件中定义的技能。
"""

from typing import Any, Dict

from src.skills import SkillLoader, SkillExecutor
from src.tools.base import BaseTool


class SkillTool(BaseTool):
    """执行技能的工具。"""

    def __init__(self):
        """初始化技能工具。"""
        # 使用 skills 模块的加载器和执行器
        self._loader = SkillLoader()
        self._executor = SkillExecutor(self._loader)
        self._skills = self._loader.load_all()

        tool_description = self._build_tool_description()
        super().__init__(name="skill", description=tool_description)

    def _build_tool_description(self) -> str:
        """构建工具描述。"""
        skills_list = []
        for skill in self._skills:
            fm = skill.frontmatter
            args_part = f"({fm.argument_hint})" if fm.argument_hint else ""
            when_part = fm.when_to_use or ""
            entry = f"- {fm.name}{args_part}: {fm.description} {when_part}".strip()
            skills_list.append(entry)

        available_skills = "\n".join(skills_list)

        return f"""Execute a skill within the main conversation

<skills_instructions>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively.

How to invoke:
- Use this tool with skill name and optional arguments
- Examples:
  - skill: "pdf" - invoke pdf skill
  - skill: "ms-office-suite:pdf" - invoke using fully qualified name

Important:
- When a skill is relevant, you MUST invoke this tool IMMEDIATELY as your first action
- NEVER just announce or mention a skill without actually calling it
</skills_instructions>

<available_skills>
{available_skills}
</available_skills>"""

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义。"""
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to execute (e.g., 'pdf', 'my-skill')",
                },
                "args": {
                    "type": "object",
                    "description": "Arguments for the skill",
                },
            },
            "required": ["skill_name"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行技能工具。"""
        skill_name = kwargs.get('skill_name') if kwargs else None
        args = kwargs.get('args', {})

        if not skill_name:
            raise ValueError(f"skill_name parameter is required. Received kwargs: {kwargs}")

        try:
            # 使用 executor 执行技能
            content = self._executor.execute(skill_name, args)

            # 获取技能信息
            skill_info = self._executor.get_skill_info(skill_name)

            return {
                "skill_name": skill_name,
                "args": args,
                "content": content,
                "allowed_tools": skill_info.get("allowed_tools", []) if skill_info else [],
            }

        except ValueError as e:
            raise ValueError(f"Skill '{skill_name}' error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error executing skill '{skill_name}': {str(e)}")

    def __repr__(self) -> str:
        return f"SkillTool(name={self.name})"
