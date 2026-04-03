"""Claude DX Hooks 通用库 - 合并配置、日志、飞书机器人、系统通知和工具函数."""
import json
import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# 配置模块
# ============================================================================

class Config:
    """配置管理类 - 应用机器人模式."""

    # 通知类型常量
    NOTIFICATION_TYPE_FEISHU = "feishu"

    def __init__(self):
        """初始化配置."""
        # 通知类型配置
        self.notification_type = self._load_config(
            "NOTIFICATION_TYPE",
            "notificationType",
            default=self.NOTIFICATION_TYPE_FEISHU
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
        required = [self.app_id, self.app_secret, self.receive_id]
        return (
            all(required) and
            self.receive_id_type in ["open_id", "chat_id", "user_id", "email"]
        )


# 全局配置实例
config = Config()


# ============================================================================
# 日志模块
# ============================================================================

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
logger = StderrLogger("claude-dx", os.getenv("LOG_LEVEL", "INFO"))


# ============================================================================
# 敏感信息过滤模块
# ============================================================================

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


def filter_sensitive_info(text: str, max_length: Optional[int] = None) -> str:
    """
    过滤敏感信息并截断文本.

    Args:
        text: 待过滤的文本
        max_length: 最大长度，超过则截断

    Returns:
        str: 过滤后的文本
    """
    if not text:
        return ""

    text = str(text)

    # 过滤敏感信息
    for pattern in SENSITIVE_PATTERNS:
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


# ============================================================================
# 格式化工具模块
# ============================================================================

def format_dict_summary(data: Dict[str, Any], max_length: int = 300) -> str:
    """
    格式化字典为摘要字符串.

    Args:
        data: 待格式化的字典
        max_length: 最大长度

    Returns:
        str: 格式化后的摘要字符串
    """
    try:
        summary_data = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 100:
                summary_data[key] = f"<text:{len(value)} chars>"
            else:
                summary_data[key] = value

        json_str = json.dumps(summary_data, ensure_ascii=False, indent=2)
        return filter_sensitive_info(json_str, max_length)
    except Exception:
        return str(data)[:max_length]


def get_project_name(project_dir: str) -> str:
    """
    从项目路径中提取最后一级目录名，用于卡片标题前缀.

    Args:
        project_dir: 项目目录路径

    Returns:
        str: 格式化的项目名前缀，如 "[anker-gsm-platform-ai] "
    """
    if not project_dir or project_dir == "Unknown":
        return ""
    name = Path(project_dir).name
    return f"[{name}] " if name else ""


def get_session_id(input_data: Dict[str, Any]) -> str:
    """
    提取会话ID.

    Args:
        input_data: 包含会话信息的输入数据

    Returns:
        str: 会话ID（最多8位）
    """
    session_id = input_data.get("session_id") or input_data.get("sessionId", "unknown")
    if len(session_id) > 8:
        return session_id[:8]
    return session_id


# ============================================================================
# 飞书机器人模块
# ============================================================================

try:
    import requests
except ImportError:
    requests = None
    logger.warning("requests module not found, Feishu notifications disabled")


class FeishuTokenManager:
    """飞书应用Token管理器 - 负责获取和缓存tenant_access_token."""

    TOKEN_API_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    def __init__(self, app_id: str, app_secret: str, cache_file: Path):
        """
        初始化Token管理器.

        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            cache_file: Token缓存文件路径
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.cache_file = cache_file
        self.token = None
        self.expire_time = None

    def get_token(self) -> str:
        """
        获取有效的token(自动刷新).

        Returns:
            str: 有效的tenant_access_token

        Raises:
            Exception: Token获取失败
        """
        # 1. 尝试从缓存加载
        if self._load_from_cache():
            if not self._is_token_expired():
                logger.debug("Using cached token")
                return self.token

        # 2. Token过期或不存在,重新获取
        logger.debug("Token expired or not found, refreshing...")
        self._refresh_token()
        return self.token

    def _load_from_cache(self) -> bool:
        """
        从文件加载缓存的token.

        Returns:
            bool: 是否成功加载
        """
        if not self.cache_file.exists():
            return False

        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            self.token = data.get("token")
            self.expire_time = data.get("expire_time")
            return bool(self.token and self.expire_time)
        except Exception as e:
            logger.warning(f"Failed to load token cache: {e}")
            return False

    def _save_to_cache(self) -> None:
        """保存token到缓存文件."""
        try:
            data = {
                "token": self.token,
                "expire_time": self.expire_time
            }
            self.cache_file.write_text(json.dumps(data), encoding="utf-8")
            # 设置文件权限为只有所有者可读写
            self.cache_file.chmod(0o600)
            logger.debug("Token saved to cache")
        except Exception as e:
            logger.warning(f"Failed to save token cache: {e}")

    def _is_token_expired(self) -> bool:
        """
        检查token是否过期(提前5分钟刷新).

        Returns:
            bool: 是否过期
        """
        if not self.expire_time:
            return True
        # 提前5分钟刷新
        return time.time() >= self.expire_time - 300

    def _refresh_token(self) -> None:
        """
        从飞书API获取新token.

        Raises:
            Exception: Token获取失败
        """
        if not requests:
            raise Exception("requests module not available")

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(
                self.TOKEN_API_URL,
                json=payload,
                timeout=10
            )
            data = response.json()

            if data.get("code") == 0:
                # 兼容不同的响应格式
                token_data = data.get("tenant_access_token") or data.get("data", {}).get("tenant_access_token")
                expire_seconds = data.get("expire") or data.get("data", {}).get("expire", 7200)

                if not token_data:
                    raise Exception("Token not found in API response")

                self.token = token_data
                self.expire_time = time.time() + expire_seconds

                # 保存到缓存
                self._save_to_cache()

                logger.debug(f"Token refreshed successfully, expires in {expire_seconds}s")
            else:
                raise Exception(f"Failed to get token: {data.get('msg', 'Unknown error')}")

        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            raise Exception(f"Token refresh failed: {e}") from e


class FeishuAppBot:
    """飞书应用机器人客户端 - 使用开放API发送消息."""

    BASE_URL = "https://open.feishu.cn/open-apis"

    # 飞书卡片 header 颜色（使用飞书模板名称）
    COLORS = {
        "blue": "blue",
        "orange": "orange",
        "green": "green",
        "red": "red",
        "yellow": "yellow",
        "purple": "purple",
        "grey": "grey",
    }

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        receive_id: str,
        receive_id_type: str = "open_id",
        cache_file: Optional[Path] = None
    ):
        """
        初始化飞书应用机器人.

        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            receive_id: 消息接收者ID
            receive_id_type: 接收者类型 (open_id/chat_id/user_id/email)
            cache_file: Token缓存文件路径
        """
        self.receive_id = receive_id
        self.receive_id_type = receive_id_type
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 1

        # 初始化Token管理器
        cache_path = cache_file or (Path.home() / ".feishu_token_cache")
        self.token_manager = FeishuTokenManager(app_id, app_secret, cache_path)

    def send_card_message(
        self,
        title: str,
        content: str,
        color: str = "blue",
    ) -> bool:
        """
        发送卡片消息到飞书.

        Args:
            title: 消息标题（显示在彩色 header 中）
            content: 消息正文
            color: header 颜色 (blue/orange/green/red/yellow/purple/grey)

        Returns:
            bool: 发送是否成功
        """
        if not requests:
            logger.error("requests module not available")
            return False

        try:
            # 构建卡片
            card = self._build_card(title, content, color)

            # 构建请求payload
            payload = {
                "receive_id": self.receive_id,
                "msg_type": "interactive",
                "content": json.dumps(card)
            }

            # 发送请求
            return self._send_message(payload)

        except Exception as e:
            # 捕获所有异常,确保不影响Hook执行
            logger.error(f"Failed to send Feishu message: {e}", exc_info=e)
            return False

    def _send_message(self, payload: Dict[str, Any]) -> bool:
        """
        发送消息到飞书API(带重试).

        Args:
            payload: 请求负载

        Returns:
            bool: 是否成功
        """
        url = f"{self.BASE_URL}/im/v1/messages"
        params = {"receive_id_type": self.receive_id_type}

        for attempt in range(1, self.max_retries + 1):
            try:
                # 获取token
                token = self.token_manager.get_token()

                # 构建请求头
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                # 发送请求
                response = requests.post(
                    url,
                    params=params,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # 检查响应
                data = response.json()

                if data.get("code") == 0:
                    logger.debug(f"Message sent successfully (attempt {attempt})")
                    return True

                # Token过期,刷新后重试
                if data.get("code") == 99991663:  # token expired
                    logger.warning("Token expired, refreshing...")
                    self.token_manager._refresh_token()
                    if attempt < self.max_retries:
                        continue

                # 限流,等待后重试
                if data.get("code") == 200001:  # rate limit
                    logger.warning(f"Rate limited, retrying (attempt {attempt}/{self.max_retries})")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * attempt)
                        continue

                # 其他错误
                logger.error(f"Feishu API error: {data.get('msg', 'Unknown error')} (code: {data.get('code')})")
                return False

            except requests.Timeout:
                logger.warning(f"Request timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return False

            except Exception as e:
                logger.error(f"Request failed: {e}", exc_info=e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return False

        return False

    def _build_card(
        self,
        title: str,
        content: str,
        color: str,
    ) -> Dict[str, Any]:
        """
        构建飞书卡片消息结构.

        Args:
            title: 标题（显示在彩色 header 中）
            content: 正文内容
            color: header 颜色 (blue/orange/green/red/yellow/purple/grey)

        Returns:
            Dict: 卡片消息结构
        """
        template = self.COLORS.get(color, "blue")

        elements = []

        # 正文
        if content:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            })

        # 底部时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": timestamp
                }
            ]
        })

        return {
            "header": {
                "template": template,
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            },
            "elements": elements
        }
