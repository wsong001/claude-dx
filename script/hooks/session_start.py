#!/usr/bin/env python3
"""SessionStart Hook - 会话开始时触发."""
import json
import os
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


class SessionStartHandler:
    """会话开始处理器."""

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
        """验证输入数据."""
        return "session_id" in input_data or "sessionId" in input_data

    def process(self, input_data: Dict[str, Any]) -> None:
        """处理Hook输入数据."""
        try:
            if not self.validate_input(input_data):
                self.logger.error("Invalid input data")
                return
            self.send_notification(input_data)
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=e)

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送会话开始通知."""
        if self.config.is_system_notification():
            self._send_system_notification()
        elif self.bot:
            self._send_feishu_notification(input_data)

    def _send_system_notification(self) -> None:
        """发送系统通知."""
        title = "🚀 Claude Code"
        content = "会话已启动"
        success = send_notification(title, content)
        if success:
            self.logger.info("System SessionStart notification sent")
        else:
            self.logger.warning("Failed to send system SessionStart notification")

    def _send_feishu_notification(self, input_data: Dict[str, Any]) -> None:
        """发送飞书通知."""
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")
        cwd = input_data.get("cwd") or os.getcwd()

        git_status = "Not a git repository"
        if input_data.get("git_repo"):
            branch = input_data.get("git_branch", "unknown")
            git_status = f"✓ Git repository (branch: {branch})"

        content = f"🚀 Claude Code 会话已启动"

        fields = [
            {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
            {"name": "工作目录", "value": f"`{cwd}`", "icon": "📁"},
            {"name": "Git状态", "value": git_status, "icon": "🔀", "highlight": not input_data.get("git_repo")},
            {"name": "启动时间", "value": timestamp, "icon": "⏰"},
        ]

        if input_data.get("user"):
            fields.append({"name": "用户", "value": input_data["user"], "icon": "👤"})

        success = self.bot.send_card_message(
            title="🎯 会话开始 | Session Start",
            content=content,
            color="blue",
            fields=fields
        )

        if success:
            self.logger.info(f"Feishu SessionStart notification sent for session {session_id}")
        else:
            self.logger.warning(f"Failed to send Feishu SessionStart notification for session {session_id}")

    def filter_sensitive_info(self, text: str, max_length: Optional[int] = None) -> str:
        """过滤敏感信息并截断文本."""
        if not text:
            return ""
        text = str(text)
        for pattern in self.SENSITIVE_PATTERNS:
            text = re.sub(
                rf'(["\']?{pattern}["\']?\s*[:=]\s*)([^,\s\]}}]+)',
                r'\1***',
                text,
                flags=re.IGNORECASE
            )
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        return text

    def get_session_id(self, input_data: Dict[str, Any]) -> str:
        """提取会话ID."""
        session_id = input_data.get("session_id") or input_data.get("sessionId", "unknown")
        if len(session_id) > 8:
            return session_id[:8]
        return session_id


def main():
    """主函数."""
    try:
        input_data = json.load(sys.stdin)
        handler = SessionStartHandler()
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
