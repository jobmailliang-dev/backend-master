"""前端解析器。

解析 Markdown 文件中的 YAML 前端。
"""

from typing import Any, Dict, Tuple


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """解析 Markdown 内容中的 YAML 前端。

    Args:
        content: 原始 Markdown 内容

    Returns:
        (前端字典, 正文内容)

    格式:
        ---
        name: skill-name
        description: skill description
        ---
        content here...
    """
    parts = content.split('---', 2)

    if len(parts) < 3:
        return {}, content.strip()

    frontmatter_content = parts[1].strip()
    body_content = parts[2].strip()

    import yaml
    try:
        frontmatter = yaml.safe_load(frontmatter_content)
        if not isinstance(frontmatter, dict):
            return {}, body_content
        return frontmatter, body_content
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")
