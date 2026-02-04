"""日志工具 - 输出到stderr避免干扰stdout."""
import sys
import logging
from datetime import datetime
from typing import Optional


class StderrLogger:
    """输出到stderr的日志记录器."""

    def __init__(self, name: str = "claude-dx", level: str = "INFO"):
        """
        初始化日志记录器.

        Args:
            name: 日志记录器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 避免重复添加handler
        if not self.logger.handlers:
            # 创建stderr handler
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.DEBUG)

            # 创建格式化器
            formatter = logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """记录ERROR级别日志."""
        self.logger.error(message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """记录CRITICAL级别日志."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)


# 全局日志实例
import os

logger = StderrLogger("claude-dx", os.getenv("LOG_LEVEL", "INFO"))
