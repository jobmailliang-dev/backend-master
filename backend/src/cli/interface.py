"""CLI 界面。

主命令行交互界面。
"""

import sys
from typing import Optional

from src.cli.input import get_input, is_empty, is_exit_command
from src.cli.output import print_welcome, print_message
from src.config.models import AppConfig
from src.core.client import LLMClient


class CLIInterface:
    """CLI 交互界面。"""

    def __init__(self, config: AppConfig):
        """初始化 CLI 界面。"""
        self.config = config
        self.client = LLMClient(
            openai_config=config.openai,
            tools_config=config.tools,
            metadata=config.get_system_metadata_dict(),
            llm_provider=config.llm_provider,
            qwen_config=config.qwen,
        )
        self.user_prefix = config.cli.user_prefix
        self.ai_prefix = config.cli.ai_prefix
        self.title = config.cli.title
        self.exit_command = config.cli.exit_command

    def run(self) -> None:
        """运行 CLI 主循环。"""
        self.print_welcome()

        while True:
            try:
                user_input = get_input(f"{self.user_prefix}: ")

                if is_exit_command(user_input, self.exit_command):
                    print("Goodbye!")
                    break

                if is_empty(user_input):
                    continue

                response = self.client.chat(user_input)
                print_message(f"{self.ai_prefix}: {response}")
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break

    def print_welcome(self) -> None:
        """打印欢迎信息。"""
        print_welcome(self.title, self.exit_command)
        print("提示：Ctrl+Enter 换行，Enter 发送，Ctrl+C 退出")


def create_cli(config: AppConfig) -> CLIInterface:
    """创建 CLI 实例。"""
    return CLIInterface(config)


def run_cli(config_path: Optional[str] = None) -> None:
    """运行 CLI 应用。"""
    from src.config.loader import load_config, ConfigurationError

    try:
        config = load_config(config_path)
        cli = create_cli(config)
        cli.run()
    except ConfigurationError as e:
        print(f"Error: {e}")
        print("Please ensure 'config.yaml' exists in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error - {e}")
        sys.exit(1)
