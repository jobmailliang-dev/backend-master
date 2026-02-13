"""配置加载器。

从 YAML 文件加载配置。
"""

from pathlib import Path
from typing import Optional

import yaml

from src.config.models import (
    AppConfig,
    OpenAIConfig,
    QwenConfig,
    ToolsConfig,
    CLIConfig,
    SystemMetadata,
    SkillMetadata,
)


class ConfigurationError(Exception):
    """配置相关错误。"""
    pass


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """从 YAML 文件加载配置。

    Args:
        config_path: 配置文件路径，默认使用项目根目录的 config.yaml

    Returns:
        AppConfig: 应用配置对象

    Raises:
        ConfigurationError: 配置文件不存在或格式错误
    """
    if config_path is None:
        # 查找项目根目录
        # 当前文件: backend/src/config/loader.py
        # 项目根目录: backend/src/config/../../../
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML format: {e}")

    # 解析 LLM provider 配置
    llm_provider = raw_config.get('llm', {}).get('provider', 'openai')

    # 解析各配置部分
    openai_config = _parse_openai_config(raw_config.get('openai', {}))
    qwen_config = _parse_qwen_config(raw_config.get('qwen', {}))
    tools_config = _parse_tools_config(raw_config.get('tools', {}))
    cli_config = _parse_cli_config(raw_config.get('cli', {}))
    system_metadata = _parse_system_metadata(raw_config.get('system_metadata', {}))
    skill_metadata = _parse_skill_metadata(raw_config.get('skill_metadata', {}))

    return AppConfig(
        llm_provider=llm_provider,
        openai=openai_config,
        qwen=qwen_config,
        tools=tools_config,
        cli=cli_config,
        system_metadata=system_metadata,
        skill_metadata=skill_metadata,
    )


def _parse_openai_config(raw: dict) -> OpenAIConfig:
    """解析 OpenAI 配置。"""
    return OpenAIConfig(
        api_url=raw.get('api_url', ''),
        api_key=raw.get('api_key', ''),
        model=raw.get('model', 'gpt-3.5-turbo'),
        max_tokens=raw.get('max_tokens', 1000),
        temperature=raw.get('temperature', 0.7),
        system_message=raw.get('system_message', 'You are a helpful assistant.'),
        use_stream=raw.get('use_stream', False),
    )


def _parse_qwen_config(raw: dict) -> QwenConfig:
    """解析 Qwen 配置。"""
    return QwenConfig(
        api_url=raw.get('api_url', ''),
        api_key=raw.get('api_key', ''),
        model=raw.get('model', 'qwen-turbo'),
        max_tokens=raw.get('max_tokens', 1000),
        temperature=raw.get('temperature', 0.7),
        system_message=raw.get('system_message', 'You are a helpful assistant.'),
        use_stream=raw.get('use_stream', True),
        enable_thinking=raw.get('enable_thinking', False),
        thinking_budget=raw.get('thinking_budget', 4000),
    )


def _parse_tools_config(raw: dict) -> ToolsConfig:
    """解析工具配置。"""
    return ToolsConfig(
        allowed_tools=raw.get('allowed_tools', []),
        max_tool_calls=raw.get('max_tool_calls', 10),
        show_tool_calls=raw.get('show_tool_calls', True),
    )


def _parse_cli_config(raw: dict) -> CLIConfig:
    """解析 CLI 配置。"""
    return CLIConfig(
        title=raw.get('title', 'LLM CLI - Chat with AI'),
        user_prefix=raw.get('user_prefix', 'You'),
        ai_prefix=raw.get('ai_prefix', 'AI'),
        exit_command=raw.get('exit_command', 'exit'),
        show_system=raw.get('show_system', False),
    )


def _parse_system_metadata(raw: dict) -> Optional[SystemMetadata]:
    """解析系统元数据，支持任意参数。"""
    if not raw:
        return None
    # 过滤 None 值，只保留有效的配置项
    extra = {k: v for k, v in raw.items() if v is not None}
    return SystemMetadata(extra=extra)


def _parse_skill_metadata(raw: dict) -> Optional[SkillMetadata]:
    """解析技能元数据，支持任意参数。"""
    if not raw:
        return None
    # 过滤 None 值，只保留有效的配置项
    extra = {k: v for k, v in raw.items() if v is not None}
    return SkillMetadata(extra=extra)
