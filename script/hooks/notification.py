#!/usr/bin/env python3
"""Notification Hook - 系统通知时触发."""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 添加common目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "common"))

from common.config import config
from common.logger import logger
from common.feishu_bot import FeishuAppBot


class NotificationHandler:
    """通知处理器."""

    SENSITIVE_PATTERNS = [
        r"api[_-]?key", r"secret", r"password", r"token",
        r"auth", r"credential", r"private[_-]?key",
    ]

    def __init__(self):
        self.config = config
        self.logger = logger
        self.bot: Optional[FeishuAppBot] = None

        if self.config.is_system_notification():
            self.logger.info("Using system notification mode")
        elif self.config.validate():
            self.bot = FeishuAppBot(
                app_id=self.config.app_id,
                app_secret=self.config.app_secret,
                receive_id=self.config.receive_id,
                receive_id_type=self.config.receive_id_type,
                cache_file=self.config.token_cache_file
            )
            self.logger.info("Using Feishu notification mode")
        else:
            self.logger.warning("Notification not configured, notifications disabled")

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "notification_type" in input_data

    def process(self, input_data: Dict[str, Any]) -> None:
        try:
            if not self.validate_input(input_data):
                self.logger.error("Invalid input data")
                return
            self.send_notification(input_data)
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=e)

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        notification_type = input_data.get("notification_type", "unknown")
        timestamp = input_data.get("timestamp", "N/A")
        message = input_data.get("message", "")
        type_config = self._get_type_config(notification_type)

        if self.config.is_system_notification():
            return  # 系统通知模式下跳过通用通知

        session_id = self.get_session_id(input_data)
        content = f"{type_config['icon']} {type_config['description']}"
        if message:
            content += f"\n💬 {message}"

        fields = [
            {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
            {"name": "通知类型", "value": notification_type, "icon": "🏷️", "highlight": notification_type == "permission_prompt"},
            {"name": "触发时间", "value": timestamp, "icon": "⏰"},
        ]

        if input_data.get("details"):
            details = self.format_dict_summary(input_data["details"], 200)
            fields.append({"name": "详细信息", "value": f"```\n{details}\n```", "icon": "📄"})

        success = self.bot.send_card_message(
            title=f"{type_config['icon']} {type_config['title']}",
            content=content,
            color=type_config['color'],
            fields=fields
        )

        if success:
            self.logger.info(f"Feishu notification sent for type {notification_type}")
        else:
            self.logger.warning(f"Failed to send Feishu notification for type {notification_type}")

    def _get_type_config(self, notification_type: str) -> Dict[str, str]:
        type_configs = {
            "permission_prompt": {
                "icon": "🔐", "title": "权限请求 | Permission Prompt",
                "description": "Claude 需要权限批准", "color": "yellow"
            },
            "idle_prompt": {
                "icon": "💤", "title": "空闲提示 | Idle Prompt",
                "description": "Claude 已闲置等待输入", "color": "blue"
            },
            "auth_success": {
                "icon": "✅", "title": "认证成功 | Auth Success",
                "description": "用户认证成功", "color": "green"
            },
            "elicitation_dialog": {
                "icon": "❓", "title": "需要输入 | Elicitation Dialog",
                "description": "系统需要用户提供信息", "color": "orange"
            }
        }
        return type_configs.get(notification_type, {
            "icon": "🔔", "title": "系统通知 | Notification",
            "description": "Claude Code 通知", "color": "blue"
        })

    def filter_sensitive_info(self, text: str, max_length: Optional[int] = None) -> str:
        if not text:
            return ""
        text = str(text)
        for pattern in self.SENSITIVE_PATTERNS:
            text = re.sub(rf'(["\']?{pattern}["\']?\s*[:=]\s*)([^,\s\]}}]+)', r'\1***', text, flags=re.IGNORECASE)
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        return text

    def format_dict_summary(self, data: Dict[str, Any], max_length: int = 300) -> str:
        try:
            summary_data = {}
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    summary_data[key] = f"<text:{len(value)} chars>"
                else:
                    summary_data[key] = value
            json_str = json.dumps(summary_data, ensure_ascii=False, indent=2)
            return self.filter_sensitive_info(json_str, max_length)
        except Exception as e:
            self.logger.error(f"Failed to format dict: {e}")
            return str(data)[:max_length]

    def get_session_id(self, input_data: Dict[str, Any]) -> str:
        session_id = input_data.get("session_id") or input_data.get("sessionId", "unknown")
        if len(session_id) > 8:
            return session_id[:8]
        return session_id


def main():
    try:
        input_data = json.load(sys.stdin)
        handler = NotificationHandler()
        handler.process(input_data)
        json.dump(input_data, sys.stdout)
        sys.stdout.flush()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        print("{}", flush=True)
    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=e)
        try:
            sys.stdin.seek(0)
            sys.stdout.write(sys.stdin.read())
            sys.stdout.flush()
        except Exception:
            print("{}", flush=True)
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
