"""技能加载器。

从文件系统中加载技能定义。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.skills.parser import Skill, SkillFrontmatter
from src.utils.frontmatter import parse_frontmatter


@dataclass
class SkillLoadError(Exception):
    """技能加载错误。"""
    skill_path: Path
    message: str


class SkillLoader:
    """技能加载器。

    从 skills 目录加载所有技能定义。
    """

    def __init__(self, skills_dir: Optional[str] = None):
        """初始化技能加载器。

        Args:
            skills_dir: 技能目录路径，默认使用项目 data/skills
        """
        if skills_dir is None:
            # 默认路径：项目根目录下的 data/skills
            # 从 backend/src/skills/loader.py 上溯 4 层到项目根目录
            self.skills_dir = Path(__file__).parent.parent.parent.parent / "data" / "skills"
        else:
            self.skills_dir = Path(skills_dir)

    def load_all(self) -> List[Skill]:
        """加载所有技能。

        Returns:
            技能列表

        Raises:
            SkillLoadError: 加载失败
        """
        skills = []

        if not self.skills_dir.exists():
            return skills

        for skill_folder in self.skills_dir.iterdir():
            if not skill_folder.is_dir():
                continue

            try:
                skill = self.load(skill_folder.name)
                if skill:
                    skills.append(skill)
            except SkillLoadError:
                continue

        return skills

    def load(self, name: str) -> Skill:
        """加载指定技能。

        Args:
            name: 技能名称（文件夹名称）

        Returns:
            技能对象

        Raises:
            SkillLoadError: 技能不存在或加载失败
        """
        skill_folder = self.skills_dir / name
        skill_file = skill_folder / "SKILL.md"

        if not skill_folder.exists():
            raise SkillLoadError(skill_folder, f"Skill folder not found: {name}")

        if not skill_file.exists():
            raise SkillLoadError(skill_folder, f"SKILL.md not found in: {name}")

        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter_dict, body = parse_frontmatter(content)

            # 验证必需字段
            if 'name' not in frontmatter_dict:
                raise SkillLoadError(skill_file, "Missing 'name' in frontmatter")

            # 构建技能对象
            frontmatter = SkillFrontmatter(
                name=frontmatter_dict.get('name'),
                description=frontmatter_dict.get('description'),
                allowed_tools=frontmatter_dict.get('allowed-tools', []),
                argument_hint=frontmatter_dict.get('argument-hint'),
                when_to_use=frontmatter_dict.get('when_to_use'),
                version=frontmatter_dict.get('version'),
                model=frontmatter_dict.get('model'),
            )

            return Skill(
                frontmatter=frontmatter,
                content=body,
                file_path=str(skill_file),
            )

        except Exception as e:
            raise SkillLoadError(skill_file, str(e))

    def list_skill_names(self) -> List[str]:
        """列出所有可用技能名称。"""
        names = []
        if self.skills_dir.exists():
            for item in self.skills_dir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    names.append(item.name)
        return sorted(names)
