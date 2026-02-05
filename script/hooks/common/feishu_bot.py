"""飞书应用机器人API封装."""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from .logger import logger

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

    # 消息颜色映射
    COLORS = {
        "blue": "#1890FF",      # SessionStart
        "orange": "#FA8C16",    # PreToolUse
        "green": "#52C41A",     # PostToolUse (成功)
        "red": "#F5222D",       # PostToolUse (失败)
        "yellow": "#FAAD14",    # PermissionRequest
        "purple": "#722ED1",    # SubagentStop
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
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        发送卡片消息到飞书.

        Args:
            title: 消息标题
            content: 消息内容
            color: 卡片颜色 (blue/orange/green/red/yellow/purple)
            fields: 字段列表,每个字段包含 {"name": "字段名", "value": "字段值"}

        Returns:
            bool: 发送是否成功
        """
        if not requests:
            logger.error("requests module not available")
            return False

        try:
            # 构建卡片
            card = self._build_card(title, content, color, fields)

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
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        构建飞书卡片消息结构(优化视觉效果版本).

        Args:
            title: 标题
            content: 内容
            color: 颜色
            fields: 字段列表

        Returns:
            Dict: 卡片消息结构
        """
        # 获取颜色代码
        color_code = self.COLORS.get(color, self.COLORS["blue"])

        # 构建卡片元素
        elements = []

        # 添加主要内容(使用 note 样式突出显示)
        if content:
            elements.append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": content
                    }
                ]
            })

        # 添加字段(使用双列布局优化空间)
        if fields:
            for field in fields:
                field_name = field.get("name", "")
                field_value = field.get("value", "")
                field_icon = field.get("icon", "📋")  # 默认图标
                highlight = field.get("highlight", False)  # 是否高亮

                # 格式化字段值
                if highlight:
                    # 高亮显示 - 使用彩色文本和粗体
                    formatted_content = f"{field_icon} **{field_name}**\n<font color='red'>{field_value}</font>" if color == "red" else f"{field_icon} **{field_name}**\n<font color='green'>✓ {field_value}</font>"
                else:
                    # 普通显示
                    formatted_content = f"{field_icon} **{field_name}**\n{field_value}"

                elements.append({
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": False,
                            "text": {
                                "tag": "lark_md",
                                "content": formatted_content
                            }
                        }
                    ]
                })

        # 添加分隔线
        if elements:
            elements.append({"tag": "hr"})

        # 添加时间戳(使用图标和灰色文本)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🕐 <font color='grey'>{timestamp}</font>"
            }
        })

        # 构建完整卡片
        return {
            "header": {
                "template": color_code,
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            },
            "elements": elements
        }
