"""基础处理器 - 提供通用功能."""
import json
import os
import re
import sys
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from common.config import config
from common.logger import logger
from common.feishu_bot import FeishuAppBot


class BaseHandler(ABC):
    """Hook处理器基类."""

    # 敏感信息正则模式
    SENSITIVE_PATTERNS = [
        r"api[_-]?key",
        r"secret",
        r"password",
        r"token",
        r"auth",
        r"credential",
        r"private[_-]?key",
    ]

    def __init__(self):
        """初始化处理器."""
        self.config = config
        self.logger = logger
        self.bot: Optional[FeishuAppBot] = None

        # 初始化飞书应用机器人
        if self.config.validate():
            self.bot = FeishuAppBot(
                app_id=self.config.app_id,
                app_secret=self.config.app_secret,
                receive_id=self.config.receive_id,
                receive_id_type=self.config.receive_id_type,
                cache_file=self.config.token_cache_file
            )
        else:
            self.logger.warning("Feishu app bot not configured, notifications disabled")

    def process(self, input_data: Dict[str, Any]) -> None:
        """
        处理Hook输入数据.

        Args:
            input_data: 从stdin读取的JSON数据
        """
        try:
            # 验证必需字段
            if not self.validate_input(input_data):
                self.logger.error("Invalid input data")
                return

            # 发送飞书通知
            if self.bot:
                self.send_notification(input_data)

        except Exception as e:
            # 捕获所有异常,确保不影响Hook执行
            self.logger.error(f"Handler error: {e}", exc_info=e)

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证输入数据.

        Args:
            input_data: 输入数据

        Returns:
            bool: 是否有效
        """
        pass

    @abstractmethod
    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """
        发送飞书通知.

        Args:
            input_data: 输入数据
        """
        pass

    def filter_sensitive_info(self, text: str, max_length: Optional[int] = None) -> str:
        """
        过滤敏感信息并截断文本.

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            str: 过滤后的文本
        """
        if not text:
            return ""

        # 转换为字符串
        text = str(text)

        # 过滤敏感字段(如果字段名匹配敏感模式,隐藏值)
        for pattern in self.SENSITIVE_PATTERNS:
            # 匹配 key: value 或 "key": "value" 格式
            text = re.sub(
                rf'(["\']?{pattern}["\']?\s*[:=]\s*)([^,\s\]}}]+)',
                r'\1***',
                text,
                flags=re.IGNORECASE
            )

        # 截断文本
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."

        return text

    def format_dict_summary(self, data: Dict[str, Any], max_length: int = 300) -> str:
        """
        格式化字典为摘要文本.

        Args:
            data: 字典数据
            max_length: 最大长度

        Returns:
            str: 格式化的摘要
        """
        try:
            # 特殊处理:如果包含大量文本内容,只显示关键信息
            summary_data = {}
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    # 长文本显示为 [长度]
                    summary_data[key] = f"<text:{len(value)} chars>"
                else:
                    summary_data[key] = value

            # 转换为JSON字符串
            json_str = json.dumps(summary_data, ensure_ascii=False, indent=2)

            # 过滤敏感信息并截断
            return self.filter_sensitive_info(json_str, max_length)

        except Exception as e:
            self.logger.error(f"Failed to format dict: {e}")
            return str(data)[:max_length]

    def get_session_id(self, input_data: Dict[str, Any]) -> str:
        """
        提取会话ID.

        Args:
            input_data: 输入数据

        Returns:
            str: 会话ID
        """
        session_id = input_data.get("session_id") or input_data.get("sessionId", "unknown")
        # 截取前8位作为简短标识
        if len(session_id) > 8:
            return session_id[:8]
        return session_id
