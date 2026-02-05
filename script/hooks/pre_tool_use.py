#!/usr/bin/env python3
"""PreToolUse Hook - 工具执行前触发."""
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


class PreToolUseHandler:
    """工具执行前处理器."""

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
        return "tool_name" in input_data and "tool_input" in input_data

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
            return  # 系统通知模式下跳过 PreToolUse

        tool_name = input_data.get("tool_name", "Unknown")
        tool_input = input_data.get("tool_input", {})
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        input_summary = self._build_input_summary(tool_name, tool_input)
        tool_icon = self._get_tool_icon(tool_name)
        content = f"{tool_icon} 准备执行工具: **{tool_name}**"

        fields = [
            {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
            {"name": "输入参数", "value": f"```\n{input_summary}\n```", "icon": "📥"},
            {"name": "执行时间", "value": timestamp, "icon": "⏰"},
        ]

        success = self.bot.send_card_message(
            title="⚙️ 工具执行前 | Pre Tool Use",
            content=content,
            color="orange",
            fields=fields
        )

        if success:
            self.logger.info(f"PreToolUse notification sent for tool {tool_name}")
        else:
            self.logger.warning(f"Failed to send PreToolUse notification for tool {tool_name}")

    def _get_tool_icon(self, tool_name: str) -> str:
        tool_icons = {
            "Bash": "💻", "Read": "📖", "Write": "✍️", "Edit": "✏️",
            "Grep": "🔍", "Glob": "🗂️", "Task": "🤖", "WebFetch": "🌐",
        }
        return tool_icons.get(tool_name, "🔧")

    def _build_input_summary(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            return self.filter_sensitive_info(command, self.config.max_param_length)
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            return f"文件: {file_path}"
        elif tool_name in ["Write", "Edit"]:
            file_path = tool_input.get("file_path", "")
            content_length = len(str(tool_input.get("content", "")))
            return f"文件: {file_path}\n内容长度: {content_length} chars"
        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            return f"模式: {pattern}\n路径: {path}"
        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            return f"模式: {pattern}"
        else:
            return self.format_dict_summary(tool_input, self.config.max_param_length)

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
        handler = PreToolUseHandler()
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
