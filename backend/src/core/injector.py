"""Injector 依赖注入配置模块。

提供全局 Injector 实例和自动扫描加载模块功能。
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from injector import Injector, Module


def _scan_modules() -> list[Module]:
    """扫描 src.modules 包下所有子模块，收集继承自 Module 的类。

    Returns:
        Module 实例列表
    """
    modules: list[Module] = []
    modules_pkg = Path(__file__).parent.parent / "modules"

    # 遍历 modules 包下的所有子包
    for importer, modname, ispkg in pkgutil.iter_modules([str(modules_pkg)]):
        if not ispkg or modname == "__pycache__":
            continue

        try:
            # 动态导入子模块
            module = importlib.import_module(f"src.modules.{modname}")

            # 遍历模块中的所有类，找出继承自 Module 的类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 检查是否是 Module 的子类，且不是 Module 本身
                if issubclass(obj, Module) and obj is not Module:
                    # 排除已实例化的模块
                    if not isinstance(obj, Module):
                        modules.append(obj())
                        print(f"[injector] Loaded module: {name}")

        except Exception as e:
            print(f"[injector] Failed to load module {modname}: {e}")

    return modules


# 动态扫描加载所有业务模块
_modules: list[Module] = _scan_modules()

# 创建全局 Injector 实例
injector: Injector = Injector(_modules)


def reload_modules() -> None:
    """重新加载模块（用于测试或动态添加模块）"""
    global _modules, injector
    _modules = _scan_modules()
    injector = Injector(_modules)


__all__ = [
    "injector",
    "reload_modules",
    "Module",
]
