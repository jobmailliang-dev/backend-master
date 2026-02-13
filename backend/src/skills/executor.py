"""技能执行器。

执行技能逻辑。
"""

import re
from typing import Any, Dict, List, Optional

from src.config.loader import load_config
from src.skills.loader import SkillLoader, SkillLoadError
from src.skills.parser import Skill


class SkillExecutor:
    """技能执行器。"""

    def __init__(self, loader: Optional[SkillLoader] = None):
        """初始化执行器。

        Args:
            loader: 技能加载器，默认使用新实例
        """
        self.loader = loader or SkillLoader()
        self._skill_cache: Dict[str, Skill] = {}
        self._system_metadata: Optional[Dict[str, str]] = None
        self._skill_metadata: Optional[Dict[str, str]] = None

    def execute(self, skill_name: str, args: Dict[str, Any] = None) -> str:
        """执行技能。

        Args:
            skill_name: 技能名称
            args: 技能参数

        Returns:
            格式化的技能内容

        Raises:
            ValueError: 技能不存在或执行失败
        """
        args = args or {}

        # 加载或获取缓存的技能
        skill = self._get_skill(skill_name)

        if not skill:
            available = self.loader.list_skill_names()
            raise ValueError(
                f"Skill '{skill_name}' not found. "
                f"Available skills: {available}"
            )

        # 格式化内容（替换占位符）
        content = self._format_content(skill, args)

        return content

    def _get_skill(self, name: str) -> Optional[Skill]:
        """获取技能（带缓存）。"""
        if name in self._skill_cache:
            return self._skill_cache[name]

        try:
            skill = self.loader.load(name)
            self._skill_cache[name] = skill
            return skill
        except SkillLoadError:
            return None

    def _get_system_metadata(self) -> Dict[str, str]:
        """获取系统元数据（懒加载）。"""
        if self._system_metadata is None:
            try:
                config = load_config()
                self._system_metadata = config.get_system_metadata_dict()
            except Exception:
                self._system_metadata = {}
        return self._system_metadata

    def _get_skill_metadata(self) -> Dict[str, str]:
        """获取技能元数据（懒加载）。"""
        if self._skill_metadata is None:
            try:
                config = load_config()
                self._skill_metadata = config.get_skill_metadata_dict()
            except Exception:
                self._skill_metadata = {}
        return self._skill_metadata

    def _format_content(self, skill: Skill, args: Dict[str, Any]) -> str:
        """格式化技能内容，替换占位符。"""
        content = skill.content

        # 获取技能目录路径，供占位符使用
        from pathlib import Path
        skill_dir = str(Path(skill.file_path).parent)

        # 合并技能元数据、skill_dir 与用户参数，用户参数优先级更高
        merged_args = {
            **self._get_skill_metadata(),
            'skill_dir': skill_dir,
            **args,
        }
        # 替换 {xxx} 占位符
        def replacer(match):
            key = match.group(1)
            return str(merged_args.get(key, match.group(0)))

        content = re.sub(r'\{(\w+)\}', replacer, content)

        # 添加技能上下文信息
        context_info = f"Base directory: {skill_dir}\n"

        return context_info + content

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能信息。"""
        skill = self._get_skill(skill_name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "description": skill.description,
            "allowed_tools": skill.allowed_tools,
            "file_path": skill.file_path,
        }

    def list_available_skills(self) -> List[str]:
        """列出所有可用技能。"""
        return self.loader.list_skill_names()

    def clear_cache(self) -> None:
        """清除技能缓存。"""
        self._skill_cache.clear()
