#!/usr/bin/env python3
"""SubagentStop Hook - 子代理停止时触发."""
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


class SubagentStopHandler:
    """子代理停止处理器."""

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
        return "agent_type" in input_data or "agent_name" in input_data

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

        agent_type = input_data.get("agent_type", "unknown")
        agent_name = input_data.get("agent_name", agent_type)
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        status = input_data.get("status", "completed")
        is_success = status in ["completed", "success"]
        status_icon = "✅" if is_success else "⚠️"
        status_text = "成功完成" if is_success else f"已停止 ({status})"

        content = f"{status_icon} 子代理已停止\n\n**代理名称**: `{agent_name}`\n**代理类型**: `{agent_type}`\n**完成状态**: {status_text}\n**会话ID**: `{session_id}`"

        fields = []

        if "summary" in input_data:
            summary = self.filter_sensitive_info(input_data["summary"], 300)
            fields.append({"name": "执行摘要", "value": summary})

        if "result" in input_data:
            result = self.filter_sensitive_info(str(input_data["result"]), 300)
            fields.append({"name": "执行结果", "value": f"```\n{result}\n```"})

        stats = []
        if "turns" in input_data:
            stats.append(f"回合数: {input_data['turns']}")
        if "duration" in input_data:
            duration_sec = input_data["duration"] / 1000
            stats.append(f"耗时: {duration_sec:.2f}s")
        if "tokens_used" in input_data:
            stats.append(f"Token使用: {input_data['tokens_used']}")

        if stats:
            fields.append({"name": "统计信息", "value": " | ".join(stats)})

        fields.append({"name": "停止时间", "value": timestamp})

        success = self.bot.send_card_message(
            title="🤖 子代理停止 | Subagent Stop",
            content=content,
            color="purple",
            fields=fields
        )

        if success:
            self.logger.info(f"SubagentStop notification sent for agent {agent_name}")
        else:
            self.logger.warning(f"Failed to send SubagentStop notification for agent {agent_name}")

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
        handler = SubagentStopHandler()
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
