"""基于 prompt_toolkit 的 CLI 输入模块。

提供跨平台的 CLI 输入支持：
- Enter：发送当前输入
- Ctrl+J：插入换行符
- Ctrl+C：取消当前输入
- 上下键：历史记录
- 中文输入/删除：原生支持
"""

import os
from typing import Callable, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory, InMemoryHistory


class PromptInput:
    """基于 prompt_toolkit 的 CLI 输入类。"""

    def __init__(
        self,
        prompt_text: str = ">>> ",
        multiline: bool = True,
        on_cancel: Optional[Callable[[], None]] = None,
        history_file: Optional[str] = None,
    ):
        self.prompt_text = prompt_text
        self.on_cancel = on_cancel
        self.bindings = self._create_key_bindings()

        # 历史记录：支持文件持久化或内存存储
        if history_file:
            history = FileHistory(history_file)
        else:
            history = InMemoryHistory()

        self.session = PromptSession(
            message=prompt_text,
            multiline=multiline,
            key_bindings=self.bindings,
            history=history,
        )

    def _create_key_bindings(self) -> KeyBindings:
        """创建快捷键绑定。"""
        kb = KeyBindings()

        @kb.add(Keys.Enter)
        def enter_handler(event):
            """Enter 发送输入。"""
            event.app.exit(result=event.app.current_buffer.text)

        @kb.add("c-j", filter=True)
        def ctrl_enter_handler(event):
            """Ctrl+Enter 插入换行。"""
            event.app.current_buffer.insert_text("\n")

        @kb.add(Keys.ControlC)
        def ctrl_c_handler(event):
            """Ctrl+C 取消。"""
            if self.on_cancel:
                self.on_cancel()
            raise KeyboardInterrupt

        return kb

    def read(self) -> str:
        """读取用户输入。"""
        try:
            return self.session.prompt()
        except KeyboardInterrupt:
            raise
        except EOFError:
            raise
