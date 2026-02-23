"""日志工具。

提供简单的日志封装，基于标准 logging 模块。
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Optional[str] = None,
    retention_days: int = 30,
) -> None:
    """配置日志系统。

    Args:
        log_dir: 日志文件目录，默认使用项目 logs 目录
        retention_days: 日志保留天数（默认 30 天）
    """
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 配置日志格式
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    )

    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 清除现有处理器
    logger.handlers.clear()

    # 文件处理器（按时间轮转，每天零点切割）
    log_file = log_path / "api.log"
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        utc=True,  # 使用 UTC 时间，确保轮转时间一致
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器（可选，便于调试）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 避免日志向上传播到根日志器产生重复输出
    logger.propagate = False

    # 设置默认级别
    logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """获取日志器实例。

    Args:
        name: 日志器名称，通常使用 __name__

    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)


# 支持直接导入 TimedRotatingFileHandler（如需自定义配置）
__all__ = ["get_logger", "setup_logging", "TimedRotatingFileHandler"]
