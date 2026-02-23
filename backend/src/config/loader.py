"""配置加载器。

从 YAML 文件加载配置，支持环境配置分离。
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.config.dotenv_loader import expand_env_in_dict
from src.config.models import (
    AppConfig,
    OpenAIConfig,
    QwenConfig,
    ToolsConfig,
    CLIConfig,
    ServerConfig,
    SystemMetadata,
)


class ConfigurationError(Exception):
    """配置相关错误。"""
    pass


def get_current_env() -> str:
    """获取当前环境名称。

    从 APP_ENV 环境变量获取，默认为 dev。

    Returns:
        str: 环境名称 (dev, prod, local)
    """
    return os.environ.get('APP_ENV', 'dev')


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典。

    override 中的值会覆盖 base 中的值，对于嵌套字典会递归合并。

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        Dict[str, Any]: 合并后的字典
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_and_merge_configs(config_dir: Path, env: str) -> Dict[str, Any]:
    """加载并合并配置文件。

    加载顺序：config.yaml -> config.{env}.yaml -> config.local.yaml
    每个后续文件会深度合并到之前的配置中。

    Args:
        config_dir: 配置目录
        env: 环境名称

    Returns:
        Dict[str, Any]: 合并后的配置字典
    """
    config: Dict[str, Any] = {}

    # 1. 加载基础配置
    base_config_path = config_dir / "config.yaml"
    if base_config_path.exists():
        try:
            with open(base_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format in {base_config_path}: {e}")

    # 2. 加载环境配置
    env_config_path = config_dir / f"config.{env}.yaml"
    if env_config_path.exists():
        try:
            with open(env_config_path, 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, env_config)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format in {env_config_path}: {e}")

    # 3. 加载本地覆盖配置
    local_config_path = config_dir / "config.local.yaml"
    if local_config_path.exists():
        try:
            with open(local_config_path, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, local_config)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format in {local_config_path}: {e}")

    return config


def load_config(config_path: Optional[str] = None, env: Optional[str] = None) -> AppConfig:
    """从 YAML 文件加载配置。

    支持环境配置分离，加载顺序为：
    1. 基础配置 config.yaml
    2. 环境配置 config.{env}.yaml
    3. 本地覆盖 config.local.yaml

    后加载的配置会深度合并到之前的配置中。

    Args:
        config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        env: 环境名称 (dev, prod, local)，默认为 get_current_env() 的返回值

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
        config_path = project_root
    else:
        config_path = Path(config_path)

    # 如果传入的是文件路径，取其父目录
    if config_path.is_file():
        config_path = config_path.parent

    # 确定环境
    if env is None:
        env = get_current_env()

    # 加载 .env 文件到 os.environ
    _load_dotenv_for_config(env=env)

    # 加载配置文件并合并
    raw_config = _load_and_merge_configs(config_path, env)

    # 替换配置中的环境变量占位符
    raw_config = expand_env_in_dict(raw_config)

    # 解析 LLM provider 配置

    # 解析 LLM provider 配置
    llm_provider = raw_config.get('llm', {}).get('provider', 'openai')

    # 解析各配置部分
    openai_config = _parse_openai_config(raw_config.get('openai', {}))
    qwen_config = _parse_qwen_config(raw_config.get('qwen', {}))
    tools_config = _parse_tools_config(raw_config.get('tools', {}))
    cli_config = _parse_cli_config(raw_config.get('cli', {}))
    server_config = _parse_server_config(raw_config.get('server', {}))
    system_metadata = _parse_system_metadata(raw_config.get('system_metadata', {}))

    return AppConfig(
        llm_provider=llm_provider,
        openai=openai_config,
        qwen=qwen_config,
        tools=tools_config,
        cli=cli_config,
        server=server_config,
        system_metadata=system_metadata,
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
        exit_command=raw.get('exit_command', 'exit'),
        show_system=raw.get('show_system', False),
    )


def _parse_server_config(raw: dict) -> Optional[ServerConfig]:
    """解析服务器配置。"""
    if not raw:
        return None
    return ServerConfig(
        host=raw.get('host', '0.0.0.0'),
        port=raw.get('port', 8000),
    )


def _load_dotenv_for_config(env: Optional[str] = None) -> None:
    """为配置加载环境变量。

    Args:
        env: 环境名称，默认使用 get_current_env()
    """
    from src.config.dotenv_loader import load_dotenv
    load_dotenv(env=env, override=False)


def _parse_system_metadata(raw: dict) -> Optional[SystemMetadata]:
    """解析系统元数据，支持任意参数。"""
    if not raw:
        return None
    # 过滤 None 值，只保留有效的配置项
    extra = {k: v for k, v in raw.items() if v is not None}
    return SystemMetadata(extra=extra)
