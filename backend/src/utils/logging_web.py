"""日志配置模块。

提供接口日志的配置模型和日志器初始化功能。
支持控制台输出和文件存储（日志轮转：每天零点切割，保留 30 天）。
"""

import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import List, Optional

# 敏感字段列表（用于脱敏）
SENSITIVE_FIELDS: List[str] = [
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "credential",
    "private_key",
    "authorization",
    "auth_token",
    "refresh_token",
    "client_secret",
]


def redact_sensitive_data(data: dict) -> dict:
    """递归脱敏敏感数据。

    Args:
        data: 待脱敏的字典数据

    Returns:
        脱敏后的字典
    """
    if not isinstance(data, dict):
        return data

    redacted = {}
    for key, value in data.items():
        # 检查字段名是否敏感
        is_sensitive = any(
            sensitive in key.lower() for sensitive in SENSITIVE_FIELDS
        )

        if is_sensitive:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value

    return redacted


class ConsoleLogFormatter(logging.Formatter):
    """控制台格式化器 - 简洁易读的格式。"""

    # 颜色转义序列
    COLORS = {
        "DEBUG": "\033[36m",    # 青色
        "INFO": "\033[32m",     # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",    # 红色
        "CRITICAL": "\033[35m", # 紫色
        "RESET": "\033[0m",     # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录。"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        reset = self.COLORS["RESET"]

        # 获取格式化后的消息
        message = record.getMessage()

        # 构建带颜色的格式
        asctime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{color}{levelname}:{reset} {asctime} {message}"


class JSONLogFormatter(logging.Formatter):
    """JSON 格式化器。

    将日志记录格式化为 JSON 字符串，便于后续分析。
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON。

        Args:
            record: 日志记录对象

        Returns:
            JSON 格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加源文件信息
        if record.pathname:
            log_data["file"] = record.pathname

        return str(log_data)  # 返回字符串，logging 会处理


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
    retention_days: int = 30,
) -> logging.Logger:
    """配置日志系统。

    Args:
        log_dir: 日志文件目录，默认使用项目 logs 目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        retention_days: 日志保留天数（默认 30 天）

    Returns:
        配置好的根日志器
    """
    # 确定日志目录
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs"

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 获取根日志器
    logger = logging.getLogger("src")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除现有处理器
    logger.handlers.clear()

    # 创建格式化器
    console_formatter = ConsoleLogFormatter()
    json_formatter = JSONLogFormatter()

    # 控制台处理器（简洁格式）
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.addHandler(console_handler)

    # 文件处理器（按时间轮转，每天零点切割）
    if file_output:
        log_file = log_path / "api.log"
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
            utc=True,  # 使用 UTC 时间，确保轮转时间一致
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.addHandler(file_handler)

    # 避免日志向上传播到根日志器产生重复输出
    logger.propagate = False

    return logger


def get_request_logger(name: str = "src") -> logging.Logger:
    """获取用于记录请求日志的日志器。

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


# 导出的接口日志器名称
API_LOGGER_NAME = "src.api"
