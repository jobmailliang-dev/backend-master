"""环境变量加载器。

支持从 .env 文件加载环境变量，实现：
1. 标准 .env 格式解析
2. 优先级：.env.local > .env
3. 为 config.yaml 和 mcp_servers.json 提供环境变量支持
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None


def get_project_root() -> Path:
    """获取项目根目录。

    当前文件位置: backend/src/config/dotenv_loader.py
    项目根目录: backend/src/config/../../../
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent.parent


def load_dotenv(env: Optional[str] = None, override: bool = False) -> Dict[str, str]:
    """从 .env 文件加载环境变量。

    加载顺序（优先级从低到高）：
    1. .env - 基础环境变量
    2. .env.{env} - 环境特定变量（如 .env.prod）
    3. .env.local - 本地覆盖变量（最高优先级）

    Args:
        env: 环境名称 (dev, prod, local)，默认从 APP_ENV 获取
        override: 是否覆盖已存在的环境变量，默认 False

    Returns:
        dict[str, str]: 加载的环境变量字典
    """
    if dotenv_values is None:
        return {}

    project_root = get_project_root()

    # 确定环境
    if env is None:
        env = os.environ.get('APP_ENV', 'dev')

    # 初始化环境变量字典
    loaded_vars: Dict[str, str] = {}

    # 1. 加载基础 .env
    base_env_path = project_root / ".env"
    if base_env_path.exists():
        loaded_vars.update(dotenv_values(base_env_path))

    # 2. 加载环境特定 .env.{env}
    env_env_path = project_root / f".env.{env}"
    if env_env_path.exists():
        loaded_vars.update(dotenv_values(env_env_path))

    # 3. 加载本地覆盖 .env.local
    local_env_path = project_root / ".env.local"
    if local_env_path.exists():
        loaded_vars.update(dotenv_values(local_env_path))

    # 4. 更新到 os.environ
    for key, value in loaded_vars.items():
        if override or key not in os.environ:
            os.environ[key] = value

    return loaded_vars


def expand_env_vars(value: str) -> str:
    """替换字符串中的 ${VAR_NAME} 为环境变量值。

    支持以下语法：
    - ${VAR_NAME} - 替换为环境变量值，不存在则保持原样
    - ${VAR_NAME:-default} - 如果 VAR_NAME 不存在，使用 default
    - ${VAR_NAME-default} - 同上，但不支持空字符串

    Args:
        value: 包含 ${VAR_NAME} 的字符串

    Returns:
        替换后的字符串
    """
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_expr = match.group(1)

        # 检查是否包含默认值语法
        if '::-' in var_expr:
            parts = var_expr.split('::-', 1)
            if len(parts) == 2:
                var_name, default_val = parts
                return os.environ.get(var_name, default_val)
        elif '::' in var_expr:
            parts = var_expr.split('::', 1)
            if len(parts) == 2:
                var_name, default_val = parts
                val = os.environ.get(var_name)
                return val if val is not None else default_val
        elif ':-' in var_expr:
            parts = var_expr.split(':-', 1)
            if len(parts) == 2:
                var_name, default_val = parts
                return os.environ.get(var_name, default_val)
        elif '-' in var_expr:
            parts = var_expr.split('-', 1)
            if len(parts) == 2:
                var_name, default_val = parts
                val = os.environ.get(var_name)
                return val if val is not None else default_val
        else:
            var_name = var_expr
            return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replacer, value)


def expand_env_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归替换字典中字符串的环境变量。

    Args:
        data: 包含环境变量占位符的字典

    Returns:
        替换后的字典
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = expand_env_vars(value)
        elif isinstance(value, dict):
            result[key] = expand_env_in_dict(value)
        elif isinstance(value, list):
            result[key] = expand_env_in_list(value)
        else:
            result[key] = value
    return result


def expand_env_in_list(data: list) -> list:
    """递归替换列表中字符串的环境变量。

    Args:
        data: 包含环境变量占位符的列表

    Returns:
        替换后的列表
    """
    if not isinstance(data, list):
        return data

    return [
        expand_env_vars(item) if isinstance(item, str)
        else expand_env_in_dict(item) if isinstance(item, dict)
        else expand_env_in_list(item) if isinstance(item, list)
        else item
        for item in data
    ]


def get_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量值。

    Args:
        var_name: 环境变量名称
        default: 默认值

    Returns:
        环境变量值或默认值
    """
    return os.environ.get(var_name, default)
