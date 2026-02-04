"""PostToolUse Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class PostToolUseHandler(BaseHandler):
    """工具执行后处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "tool_name" in input_data and "tool_result" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送工具执行后通知."""
        tool_name = input_data.get("tool_name", "Unknown")
        tool_result = input_data.get("tool_result", {})
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 判断执行状态
        is_success, status_text = self._check_status(tool_result)
        color = "green" if is_success else "red"
        status_icon = "✅" if is_success else "❌"

        # 构建输出摘要
        output_summary = self._build_output_summary(tool_result, is_success)

        # 获取工具图标
        tool_icon = self._get_tool_icon(tool_name)

        # 构建消息内容
        content = f"{status_icon} 工具执行完成: {tool_icon} **{tool_name}**\n📊 状态: {status_text}"

        # 构建字段列表(添加图标和高亮)
        fields = [
            {
                "name": "会话ID",
                "value": f"`{session_id}`",
                "icon": "🎯"
            },
            {
                "name": "执行结果",
                "value": f"```\n{output_summary}\n```",
                "icon": "📤",
                "highlight": not is_success  # 失败时高亮
            },
            {
                "name": "完成时间",
                "value": timestamp,
                "icon": "⏰"
            },
        ]

        # 添加执行耗时(如果有)
        if "duration" in input_data:
            duration = input_data["duration"]
            duration_sec = duration / 1000
            fields.append({
                "name": "执行耗时",
                "value": f"**{duration_sec:.2f}s** ({duration}ms)",
                "icon": "⏱️"
            })

        # 发送通知
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

    def _check_status(self, tool_result: Dict[str, Any]) -> tuple[bool, str]:
        """
        检查工具执行状态.

        Args:
            tool_result: 工具结果

        Returns:
            tuple: (是否成功, 状态文本)
        """
        # 检查是否有错误
        if "error" in tool_result and tool_result["error"]:
            return False, "失败 (Error)"

        # 检查退出码(针对Bash等命令行工具)
        if "exit_code" in tool_result:
            exit_code = tool_result["exit_code"]
            if exit_code != 0:
                return False, f"失败 (Exit code: {exit_code})"

        # 检查状态字段
        if "status" in tool_result:
            status = tool_result["status"]
            if status == "error" or status == "failed":
                return False, f"失败 (Status: {status})"

        return True, "成功"

    def _build_output_summary(self, tool_result: Dict[str, Any], is_success: bool) -> str:
        """
        构建输出摘要.

        Args:
            tool_result: 工具结果
            is_success: 是否成功

        Returns:
            str: 输出摘要
        """
        # 如果失败,优先显示错误信息
        if not is_success:
            error_msg = tool_result.get("error") or tool_result.get("stderr", "Unknown error")
            return self.filter_sensitive_info(str(error_msg), self.config.max_output_length)

        # 成功时显示输出
        output = tool_result.get("output") or tool_result.get("stdout", "")

        # 如果输出为空,显示提示
        if not output:
            return "(无输出)"

        # 过滤敏感信息并截断
        return self.filter_sensitive_info(str(output), self.config.max_output_length)
