#!/usr/bin/env python3
"""Stop Hook - Claude 完成响应时触发."""
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
from common.system_notifier import send_notification


class StopHandler:
    """停止处理器."""

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
        return "session_id" in input_data or "sessionId" in input_data

    def process(self, input_data: Dict[str, Any]) -> None:
        try:
            if not self.validate_input(input_data):
                self.logger.error("Invalid input data")
                return
            self.send_notification(input_data)
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=e)

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")
        reason = input_data.get("reason", "completed")
        stop_type = input_data.get("stop_type", "normal")

        if stop_type == "error":
            color = "red"
            icon = "❌"
            status = "异常停止"
        elif stop_type == "interrupted":
            color = "yellow"
            icon = "⏸️"
            status = "用户中断"
        else:
            color = "green"
            icon = "✅"
            status = "正常完成"

        if self.config.is_system_notification():
            self._send_system_notification(icon, status)
        elif self.bot:
            self._send_feishu_notification(input_data, session_id, icon, status, reason, timestamp, stop_type, color)

    def _send_system_notification(self, icon: str, status: str) -> None:
        title = f"{icon} Claude Code"
        content = f"会话已结束 - {status}"
        success = send_notification(title, content)
        if success:
            self.logger.info("System stop notification sent")
        else:
            self.logger.warning("Failed to send system stop notification")

    def _send_feishu_notification(self, input_data, session_id, icon, status, reason, timestamp, stop_type, color) -> None:
        content = f"{icon} Claude 已完成响应\n📊 状态: {status}"

        fields = [
            {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
            {"name": "停止原因", "value": reason, "icon": "💡", "highlight": stop_type == "error"},
            {"name": "完成时间", "value": timestamp, "icon": "⏰"},
        ]

        if "stats" in input_data:
            stats = input_data["stats"]
            stats_lines = []
            if "turns" in stats:
                stats_lines.append(f"🔄 回合数: **{stats['turns']}**")
            if "tokens" in stats:
                stats_lines.append(f"🎫 Tokens: **{stats['tokens']}**")
            if "duration" in stats:
                duration_sec = stats['duration'] / 1000
                stats_lines.append(f"⏱️ 耗时: **{duration_sec:.1f}s**")
            if stats_lines:
                fields.append({"name": "统计信息", "value": "\n".join(stats_lines), "icon": "📈"})

        if input_data.get("error"):
            error_msg = self.filter_sensitive_info(str(input_data["error"]), 200)
            fields.append({"name": "错误信息", "value": f"```\n{error_msg}\n```", "icon": "⚠️", "highlight": True})

        success = self.bot.send_card_message(
            title="🏁 会话停止 | Stop",
            content=content,
            color=color,
            fields=fields
        )

        if success:
            self.logger.info(f"Feishu Stop notification sent for session {session_id}")
        else:
            self.logger.warning(f"Failed to send Feishu Stop notification for session {session_id}")

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
        handler = StopHandler()
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
