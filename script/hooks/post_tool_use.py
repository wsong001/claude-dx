#!/usr/bin/env python3
"""PostToolUse Hook - 工具执行后触发."""
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


class PostToolUseHandler:
    """工具执行后处理器."""

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
        return "tool_name" in input_data and "tool_result" in input_data

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

        tool_name = input_data.get("tool_name", "Unknown")
        tool_result = input_data.get("tool_result", {})
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        is_success, status_text = self._check_status(tool_result)
        color = "green" if is_success else "red"
        status_icon = "✅" if is_success else "❌"

        output_summary = self._build_output_summary(tool_result, is_success)
        tool_icon = self._get_tool_icon(tool_name)
        content = f"{status_icon} 工具执行完成: {tool_icon} **{tool_name}**\n📊 状态: {status_text}"

        fields = [
            {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
            {"name": "执行结果", "value": f"```\n{output_summary}\n```", "icon": "📤", "highlight": not is_success},
            {"name": "完成时间", "value": timestamp, "icon": "⏰"},
        ]

        if "duration" in input_data:
            duration = input_data["duration"]
            duration_sec = duration / 1000
            fields.append({"name": "执行耗时", "value": f"**{duration_sec:.2f}s** ({duration}ms)", "icon": "⏱️"})

        success = self.bot.send_card_message(
            title=f"{'✓' if is_success else '✗'} 工具执行后 | Post Tool Use",
            content=content,
            color=color,
            fields=fields
        )

        if success:
            self.logger.info(f"PostToolUse notification sent for tool {tool_name}")
        else:
            self.logger.warning(f"Failed to send PostToolUse notification for tool {tool_name}")

    def _get_tool_icon(self, tool_name: str) -> str:
        tool_icons = {
            "Bash": "💻", "Read": "📖", "Write": "✍️", "Edit": "✏️",
            "Grep": "🔍", "Glob": "🗂️", "Task": "🤖", "WebFetch": "🌐",
        }
        return tool_icons.get(tool_name, "🔧")

    def _check_status(self, tool_result: Dict[str, Any]) -> tuple:
        if "error" in tool_result and tool_result["error"]:
            return False, "失败 (Error)"
        if "exit_code" in tool_result:
            exit_code = tool_result["exit_code"]
            if exit_code != 0:
                return False, f"失败 (Exit code: {exit_code})"
        if "status" in tool_result:
            status = tool_result["status"]
            if status == "error" or status == "failed":
                return False, f"失败 (Status: {status})"
        return True, "成功"

    def _build_output_summary(self, tool_result: Dict[str, Any], is_success: bool) -> str:
        if not is_success:
            error_msg = tool_result.get("error") or tool_result.get("stderr", "Unknown error")
            return self.filter_sensitive_info(str(error_msg), self.config.max_output_length)

        output = tool_result.get("output") or tool_result.get("stdout", "")
        if not output:
            return "(无输出)"
        return self.filter_sensitive_info(str(output), self.config.max_output_length)

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
        handler = PostToolUseHandler()
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
