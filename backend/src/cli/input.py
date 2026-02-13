"""输入处理模块。

处理用户 CLI 输入，支持多行输入：
- Enter：发送当前输入
- Ctrl+Enter：插入换行符
- Ctrl+C：取消/退出
- 中文输入/删除：原生支持
"""

import sys

from src.cli.prompt_input import PromptInput


def get_input(prompt: str = "") -> str:
    """获取用户输入，支持多行输入。

    - Enter：发送文本
    - Ctrl+Enter：换行
    - Ctrl+C：取消/退出

    Args:
        prompt: 输入提示符

    Returns:
        用户输入的字符串
    """
    try:
        input_obj = PromptInput(prompt_text=prompt)
        result = input_obj.read()

        if is_exit_command(result, "exit"):
            raise KeyboardInterrupt

        return result

    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        sys.exit(0)


def is_exit_command(input_text: str, exit_cmd: str) -> bool:
    """检查是否是退出命令。"""
    return input_text.lower() == exit_cmd.lower()


def is_empty(input_text: str) -> bool:
    """检查输入是否为空。"""
    return not input_text or input_text.strip() == ""
