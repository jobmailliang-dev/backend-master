"""
Application initializer module.

This module contains classes responsible for initializing various aspects
of the application such as environment variables, logging system, Python path, and configuration.
"""

import importlib
import inspect
import pkgutil
import sys
import os
from pathlib import Path
from typing import Optional, Type, TypeVar
import logging

from injector import Injector, Module

T = TypeVar("T")

# Import the dotenv loader functionality
from src.config.dotenv_loader import load_dotenv
from src.config.loader import load_config
from src.config.models import AppConfig


# 全局配置变量
_app_config: Optional[AppConfig] = None


class EnvironmentLoader:
    """
    Handles environment variable loading from .env files.
    """

    @staticmethod
    def setup_env():
        """
        Load environment variables from .env files based on APP_ENV environment variable.

        This function attempts to load environment variables from:
        1. .env - base environment variables
        2. .env.{APP_ENV} - environment-specific variables
        3. .env.local - local overrides (highest priority)

        The function will silently continue if loading fails to avoid crashing the application.
        """
        try:
            env = os.environ.get("APP_ENV", "dev")
            print(f"Loading environment variables for {env}")
            load_dotenv(override=False, env=env)
        except Exception as e:
            print(f"Warning: Failed to load environment variables: {e}")


class LoggingInitializer:
    """
    Handles logging system initialization.
    """

    @staticmethod
    def setup_logger(
        log_dir: Optional[str] = None,
        log_level: Optional[str] = None,
        retention_days: int = 30
    ):
        """
        Initialize the logging system with file rotation and console output.

        Args:
            log_dir: Directory for log files, defaults to 'logs' in project root
            log_level: Logging level, defaults to INFO or LOG_LEVEL environment variable
            retention_days: Number of days to retain log files
        """
        # Set up log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(exist_ok=True)

        # Set up log level
        if log_level is None:
            log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

        # Convert string log level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(numeric_level)

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create and configure file handler with daily rotation
        log_file = log_dir / "app.log"
        from logging.handlers import TimedRotatingFileHandler

        file_handler = TimedRotatingFileHandler(
            str(log_file),
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)

        # Create and configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)

        # Add handlers to root logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log initialization
        logging.info(f"Logging initialized. Level: {log_level}, Directory: {log_dir}")


class PythonPathInitializer:
    """
    Handles Python path setup to ensure modules can be imported correctly.
    """

    @staticmethod
    def setup_python_path():
        """
        Add the project root directory to Python path if not already present.

        This ensures that modules in the project can be imported correctly,
        especially when running from different working directories.
        """
        # Get project root directory (going up three levels from this file)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # src/core/ -> src/ -> backend/ -> project root

        # Convert to absolute path to ensure consistency
        project_root_abs = project_root.resolve()

        # Check if project root is already in sys.path
        if str(project_root_abs) not in sys.path:
            sys.path.insert(0, str(project_root_abs))
            logging.info(f"Added project root to Python path: {project_root_abs}")
        else:
            logging.debug(f"Project root already in Python path: {project_root_abs}")


class ConfigInitializer:
    """
    Handles application configuration loading.
    """

    _config: Optional[AppConfig] = None
    _env: Optional[str] = None

    @classmethod
    def setup_config(cls, env: Optional[str] = None) -> AppConfig:
        """
        Load application configuration.

        Args:
            env: Environment name (dev, prod, local), defaults to APP_ENV or 'dev'

        Returns:
            AppConfig: Application configuration object
        """
        if cls._config is not None:
            logging.debug("Config already loaded, returning cached config")
            return cls._config

        # Determine environment
        effective_env = env if env else os.environ.get("APP_ENV", "dev")
        cls._env = effective_env

        print(f"Loading config for environment: {effective_env}")
        cls._config = load_config(env=effective_env)

        logging.info(f"Config loaded for environment: {effective_env}")
        return cls._config

    @classmethod
    def get_config(cls) -> AppConfig:
        """
        Get the loaded configuration.

        Returns:
            AppConfig: Application configuration object

        Raises:
            RuntimeError: If config has not been loaded yet
        """
        if cls._config is None:
            raise RuntimeError("Config not loaded yet. Call setup_config() first.")
        return cls._config

    @classmethod
    def reload_config(cls, env: Optional[str] = None) -> AppConfig:
        """
        Reload configuration (useful for testing or dynamic config changes).

        Args:
            env: Environment name, defaults to current environment

        Returns:
            AppConfig: Reloaded configuration object
        """
        cls._config = None
        effective_env = env if env else cls._env
        return cls.setup_config(effective_env)


class InjectorModuleInitializer:
    """模块依赖注入初始化器。

    扫描 src.modules 包下的所有子模块，收集继承自 Module 的类，
    并创建全局 Injector 实例。
    """

    _injector: Optional["Injector"] = None

    @classmethod
    def _scan_modules(cls) -> list[Module]:
        """从 modules/__init__.py 中获取所有 Module 类并实例化。

        Returns:
            Module 实例列表
        """
        modules: list[Module] = []

        try:
            # 导入 modules 包
            import src.modules as modules_module
            from src.modules import __all__ as modules_all

            # 遍历 __all__ 中的所有名称
            for module_class_name in modules_all:
                # 从 modules 包中获取实际的类对象
                module_class = getattr(modules_module, module_class_name, None)
                # 确保获取到的是类而不是其他对象
                if isinstance(module_class, type):
                    # 检查是否是 Module 的子类
                    if issubclass(module_class, Module) and module_class is not Module:
                        try:
                            # 创建类的实例
                            module_instance = module_class()
                            modules.append(module_instance)
                            print(f"[initializer] Loaded module: {module_class_name}")
                        except Exception as e:
                            print(f"[initializer] Warning: Failed to instantiate {module_class_name}: {e}")
                else:
                    print(f"[initializer] Warning: {module_class_name} is not a class, skipping...")

        except ImportError as e:
            print(f"[initializer] Failed to import modules: {e}")

        return modules

    @classmethod
    def init_modules(cls) -> None:
        """初始化所有模块的依赖注入容器。"""
        if cls._injector is not None:
            logging.debug("Modules already initialized, skipping")
            return
        cls._injector = Injector(cls._scan_modules())
        logging.info("Module dependency injection initialized")

    @classmethod
    def get_injector(cls) -> "Injector":
        """获取全局 Injector 实例。"""
        if cls._injector is None:
            raise RuntimeError("Modules not initialized yet. Call init_modules() first.")
        return cls._injector

    @classmethod
    def get_service(cls, service_class: Type[T]) -> T:
        """从 Injector 获取服务实例。

        Args:
            service_class: 服务类类型

        Returns:
            服务实例
        """
        return cls.get_injector().get(service_class)


class ApplicationInitializer:
    """
    Main application initializer that orchestrates all initialization steps.

    This class provides a centralized way to initialize the application
    by calling all necessary initialization steps in the correct order.
    """

    @staticmethod
    def initialize(env: Optional[str] = None):
        """
        Perform all initialization steps in the correct order.

        The order is important:
        1. Load environment variables first (needed for configuration)
        2. Set up logging system
        3. Configure Python path
        4. Load application configuration
        5. Initialize module dependency injection

        Args:
            env: Environment name (dev, prod, local), defaults to APP_ENV or 'dev'

        Returns:
            AppConfig: Loaded application configuration
        """
        # Step 1: Load environment variables
        EnvironmentLoader.setup_env()

        # Step 2: Initialize logging system
        LoggingInitializer.setup_logger()

        # Step 3: Setup Python path
        PythonPathInitializer.setup_python_path()

        # Step 4: Load application configuration
        global _app_config
        _app_config = ConfigInitializer.setup_config(env)

        # Step 5: Initialize module dependency injection
        InjectorModuleInitializer.init_modules()

        logging.info("Application initialization completed successfully")


def get_app_config() -> AppConfig:
    """
    Get the global application configuration.

    Returns:
        AppConfig: Application configuration

    Raises:
        RuntimeError: If config has not been loaded yet
    """
    global _app_config
    if _app_config is None:
        # 尝试从 ConfigInitializer 获取
        _app_config = ConfigInitializer.get_config()
    return _app_config


def get_injector():
    """获取全局 Injector 实例。

    委托给 InjectorModuleInitializer.get_injector()。
    """
    return InjectorModuleInitializer.get_injector()


def get_service(service_class: Type[T]) -> T:
    """从 Injector 获取服务实例。

    委托给 InjectorModuleInitializer.get_service()。

    Args:
        service_class: 服务类类型

    Returns:
        服务实例
    """
    return InjectorModuleInitializer.get_service(service_class)

