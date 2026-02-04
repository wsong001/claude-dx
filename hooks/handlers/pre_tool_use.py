"""PreToolUse Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class PreToolUseHandler(BaseHandler):
    """工具执行前处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "tool_name" in input_data and "tool_input" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送工具执行前通知."""
        tool_name = input_data.get("tool_name", "Unknown")
        tool_input = input_data.get("tool_input", {})
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 构建工具输入摘要
        input_summary = self._build_input_summary(tool_name, tool_input)

        # 获取工具图标
        tool_icon = self._get_tool_icon(tool_name)

        # 构建消息内容
        content = f"{tool_icon} 准备执行工具: **{tool_name}**"

        # 构建字段列表(添加图标)
        fields = [
            {
                "name": "会话ID",
                "value": f"`{session_id}`",
                "icon": "🎯"
            },
            {
                "name": "输入参数",
                "value": f"```\n{input_summary}\n```",
                "icon": "📥"
            },
            {
                "name": "执行时间",
                "value": timestamp,
                "icon": "⏰"
            },
        ]

        # 发送通知
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
        """
        获取工具对应的图标.

        Args:
            tool_name: 工具名称

        Returns:
            str: 图标
        """
        tool_icons = {
            "Bash": "💻",
            "Read": "📖",
            "Write": "✍️",
            "Edit": "✏️",
            "Grep": "🔍",
            "Glob": "🗂️",
            "Task": "🤖",
            "WebFetch": "🌐",
        }
        return tool_icons.get(tool_name, "🔧")

    def _build_input_summary(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        构建工具输入摘要.

        Args:
            tool_name: 工具名称
            tool_input: 工具输入

        Returns:
            str: 输入摘要
        """
        # 特殊处理不同工具的输入
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
            # 默认处理:格式化整个输入
            return self.format_dict_summary(tool_input, self.config.max_param_length)
