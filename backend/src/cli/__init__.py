"""CLI 交互模块。

提供用户界面和输入输出处理。
"""

from src.cli.interface import CLIInterface
from src.cli.output import set_printer_mode

 # 切换到 Rich 美化模式
# set_printer_mode("rich")

__all__ = ['CLIInterface']

