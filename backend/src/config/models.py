"""配置数据模型。

定义应用配置的数据类。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OpenAIConfig:
    """OpenAI API 配置。"""
    api_url: str
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    system_message: str = "You are a helpful assistant."
    use_stream: bool = False


@dataclass
class QwenConfig:
    """Qwen API 配置。"""
    api_url: str
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    system_message: str = "You are a helpful assistant."
    use_stream: bool = True
    enable_thinking: bool = False
    thinking_budget: int = 4000


@dataclass
class ToolsConfig:
    """工具系统配置。"""
    allowed_tools: List[str] = field(default_factory=list)
    max_tool_calls: int = 10
    show_tool_calls: bool = True


@dataclass
class CLIConfig:
    """CLI 界面配置。"""
    title: str = "LLM CLI"
    user_prefix: str = "You"
    ai_prefix: str = "AI"
    exit_command: str = "exit"
    show_system: bool = False


@dataclass
class SystemMetadata:
    """系统元数据配置，支持任意参数。"""
    extra: Dict[str, str] = field(default_factory=dict)

    def get_metadata_dict(self) -> Dict[str, str]:
        """获取元数据字典。"""
        return self.extra.copy()


@dataclass
class SkillMetadata:
    """技能元数据配置，支持任意参数。"""
    extra: Dict[str, str] = field(default_factory=dict)

    def get_metadata_dict(self) -> Dict[str, str]:
        """获取元数据字典。"""
        return self.extra.copy()


@dataclass
class AppConfig:
    """应用完整配置。"""
    llm_provider: str = "openai"
    openai: Optional[OpenAIConfig] = None
    qwen: Optional[QwenConfig] = None
    tools: Optional[ToolsConfig] = None
    cli: Optional[CLIConfig] = None
    system_metadata: Optional[SystemMetadata] = None
    skill_metadata: Optional[SkillMetadata] = None

    def get_system_metadata_dict(self) -> Dict[str, str]:
        """获取系统元数据字典。"""
        if self.system_metadata:
            return self.system_metadata.get_metadata_dict()
        return {}

    def get_skill_metadata_dict(self) -> Dict[str, str]:
        """获取技能元数据字典。"""
        if self.skill_metadata:
            return self.skill_metadata.get_metadata_dict()
        return {}
