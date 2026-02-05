#!/usr/bin/env python3
"""PermissionRequest Hook - 权限请求时触发."""
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


class PermissionRequestHandler:
    """权限请求处理器."""

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
        return "permission_type" in input_data or "tool_name" in input_data

    def process(self, input_data: Dict[str, Any]) -> None:
        try:
            if not self.validate_input(input_data):
                self.logger.error("Invalid input data")
                return
            self.send_notification(input_data)
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=e)

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        if self.config.is_system_notification():
            return

        permission_type = input_data.get("permission_type", "unknown")
        tool_name = input_data.get("tool_name", "Unknown")
        resource = input_data.get("resource", "")
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        content = f"🔐 需要用户审批\n\n**权限类型**: `{permission_type}`\n**工具名称**: `{tool_name}`\n**会话ID**: `{session_id}`"

        fields = []

        if resource:
            resource_summary = self.filter_sensitive_info(resource, 200)
            fields.append({"name": "请求资源", "value": f"`{resource_summary}`"})

        if "action" in input_data:
            fields.append({"name": "请求操作", "value": input_data["action"]})

        if "description" in input_data:
            fields.append({"name": "说明", "value": input_data["description"]})

        fields.append({"name": "请求时间", "value": timestamp})
        fields.append({"name": "⚠️ 注意", "value": "请在Claude Code中审批此权限请求"})

        success = self.bot.send_card_message(
            title="🔒 权限请求 | Permission Request",
            content=content,
            color="yellow",
            fields=fields
        )

        if success:
            self.logger.info(f"PermissionRequest notification sent for {permission_type}")
        else:
            self.logger.warning(f"Failed to send PermissionRequest notification for {permission_type}")

    def filter_sensitive_info(self, text: str, max_length: Optional[int] = None) -> str:
        if not text:
            return ""
        text = str(text)
        for pattern in self.SENSITIVE_PATTERNS:
            text = re.sub(rf'(["\']?{pattern}["\']?\s*[:=]\s*)([^,\s\]}}]+)', r'\1***', text, flags=re.IGNORECASE)
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        return text

    def get_session_id(self, input_data: Dict[str, Any]) -> str:
        session_id = input_data.get("session_id") or input_data.get("sessionId", "unknown")
        if len(session_id) > 8:
            return session_id[:8]
        return session_id


def main():
    try:
        input_data = json.load(sys.stdin)
        handler = PermissionRequestHandler()
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
