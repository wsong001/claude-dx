"""配置加载器 - 从 ~/.claude/settings.local.json 读取应用机器人配置."""
import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """配置管理类 - 应用机器人模式."""

    # 通知类型常量
    NOTIFICATION_TYPE_SYSTEM = "system"
    NOTIFICATION_TYPE_FEISHU = "feishu"

    def __init__(self):
        """初始化配置."""
        # 通知类型配置（system 或 feishu）
        self.notification_type = self._load_config(
            "NOTIFICATION_TYPE",
            "notificationType",
            default=self.NOTIFICATION_TYPE_SYSTEM  # 默认使用系统通知
        )

        # 飞书应用机器人配置
        self.app_id = self._load_config("FEISHU_APP_ID", "feishuAppId")
        self.app_secret = self._load_config("FEISHU_APP_SECRET", "feishuAppSecret")
        self.receive_id = self._load_config("FEISHU_RECEIVE_ID", "feishuReceiveId")
        self.receive_id_type = self._load_config(
            "FEISHU_RECEIVE_ID_TYPE",
            "feishuReceiveIdType",
            default="open_id"  # 默认发送给用户
        )

        # 其他配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.timeout = int(os.getenv("TIMEOUT", "10"))
        self.max_param_length = 300  # 参数摘要最大长度
        self.max_output_length = 500  # 输出摘要最大长度

        # Token缓存路径
        self.token_cache_file = Path.home() / ".feishu_token_cache"

    def _load_config(
        self,
        env_key: str,
        config_key: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        从环境变量或配置文件加载配置值.

        优先级: 环境变量 > settings.local.json > settings.json > 默认值

        Args:
            env_key: 环境变量名
            config_key: 配置文件中的键名
            default: 默认值

        Returns:
            Optional[str]: 配置值
        """
        # 1. 环境变量(最高优先级)
        value = os.getenv(env_key)
        if value:
            return value

        # 2. settings.local.json
        local_config = Path.home() / ".claude/settings.local.json"
        if local_config.exists():
            try:
                data = json.loads(local_config.read_text(encoding="utf-8"))
                value = data.get(config_key)
                if value:
                    return value
            except (json.JSONDecodeError, IOError):
                pass

        # 3. settings.json (备用)
        global_config = Path.home() / ".claude/settings.json"
        if global_config.exists():
            try:
                data = json.loads(global_config.read_text(encoding="utf-8"))
                value = data.get(config_key)
                if value:
                    return value
            except (json.JSONDecodeError, IOError):
                pass

        # 4. 默认值
        return default

    def _load_bool_config(
        self,
        env_key: str,
        config_key: str,
        default: bool = False
    ) -> bool:
        """
        从环境变量或配置文件加载布尔值配置.

        Args:
            env_key: 环境变量名
            config_key: 配置文件中的键名
            default: 默认值

        Returns:
            bool: 配置值
        """
        # 1. 环境变量
        env_value = os.getenv(env_key)
        if env_value:
            return env_value.lower() in ("true", "1", "yes", "on")

        # 2. 配置文件
        value = self._load_config(env_key, config_key)
        if value is not None:
            # 处理布尔类型（配置文件中可能是true/false）
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")

        # 3. 默认值
        return default

    def _load_list_config(
        self,
        env_key: str,
        config_key: str,
        default: list = None
    ) -> list:
        """
        从环境变量或配置文件加载列表配置.

        Args:
            env_key: 环境变量名
            config_key: 配置文件中的键名
            default: 默认值

        Returns:
            list: 配置值
        """
        if default is None:
            default = []

        # 1. 环境变量（逗号分隔）
        env_value = os.getenv(env_key)
        if env_value:
            return [item.strip() for item in env_value.split(",")]

        # 2. 配置文件
        local_config = Path.home() / ".claude/settings.local.json"
        if local_config.exists():
            try:
                data = json.loads(local_config.read_text(encoding="utf-8"))
                value = data.get(config_key)
                if isinstance(value, list):
                    return value
            except (json.JSONDecodeError, IOError):
                pass

        # 3. settings.json (备用)
        global_config = Path.home() / ".claude/settings.json"
        if global_config.exists():
            try:
                data = json.loads(global_config.read_text(encoding="utf-8"))
                value = data.get(config_key)
                if isinstance(value, list):
                    return value
            except (json.JSONDecodeError, IOError):
                pass

        # 4. 默认值
        return default

    def validate(self) -> bool:
        """
        验证配置是否完整.

        Returns:
            bool: 配置是否有效
        """
        # 如果是系统通知，无需验证飞书配置
        if self.notification_type == self.NOTIFICATION_TYPE_SYSTEM:
            return True

        # 如果是飞书通知，验证飞书配置
        required = [self.app_id, self.app_secret, self.receive_id]
        return (
            all(required) and
            self.receive_id_type in ["open_id", "chat_id", "user_id", "email"]
        )

    def is_system_notification(self) -> bool:
        """
        检查是否使用系统通知.

        Returns:
            bool: 是否使用系统通知
        """
        return self.notification_type == self.NOTIFICATION_TYPE_SYSTEM

    def is_feishu_notification(self) -> bool:
        """
        检查是否使用飞书通知.

        Returns:
            bool: 是否使用飞书通知
        """
        return self.notification_type == self.NOTIFICATION_TYPE_FEISHU


# 全局配置实例
config = Config()
