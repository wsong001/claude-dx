"""Stop Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class StopHandler(BaseHandler):
    """停止处理器 - Claude 完成响应时触发."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        # Stop hook 通常总是有效的
        return "session_id" in input_data or "sessionId" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送停止通知."""
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 获取停止原因
        reason = input_data.get("reason", "completed")
        stop_type = input_data.get("stop_type", "normal")

        # 根据停止类型设置颜色和图标
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

        # 根据通知模式选择发送方式
        if self.config.is_system_notification():
            self._send_system_notification(icon, status, reason)
        elif self.bot:
            self._send_feishu_notification(input_data, session_id, icon, status, reason, timestamp, stop_type, color)

    def _send_system_notification(self, icon: str, status: str, reason: str) -> None:
        """发送系统通知."""
        title = f"{icon} Claude Code"
        content = f"会话已结束 - {status}"

        success = self.send_system_notification(title, content)

        if success:
            self.logger.info("System stop notification sent")
        else:
            self.logger.warning("Failed to send system stop notification")

    def _send_feishu_notification(
        self,
        input_data: Dict[str, Any],
        session_id: str,
        icon: str,
        status: str,
        reason: str,
        timestamp: str,
        stop_type: str,
        color: str
    ) -> None:
        """发送飞书通知."""
        # 构建消息内容
        content = f"{icon} Claude 已完成响应\n📊 状态: {status}"

        # 构建字段列表(添加图标和高亮)
        fields = [
            {
                "name": "会话ID",
                "value": f"`{session_id}`",
                "icon": "🎯"
            },
            {
                "name": "停止原因",
                "value": reason,
                "icon": "💡",
                "highlight": stop_type == "error"  # 错误时高亮
            },
            {
                "name": "完成时间",
                "value": timestamp,
                "icon": "⏰"
            },
        ]

        # 添加统计信息(如果有)
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
                fields.append({
                    "name": "统计信息",
                    "value": "\n".join(stats_lines),
                    "icon": "📈"
                })

        # 添加错误信息(如果有)
        if input_data.get("error"):
            error_msg = self.filter_sensitive_info(str(input_data["error"]), 200)
            fields.append({
                "name": "错误信息",
                "value": f"```\n{error_msg}\n```",
                "icon": "⚠️",
                "highlight": True  # 错误信息总是高亮
            })

        # 发送通知
        success = self.bot.send_card_message(
            title=f"🏁 会话停止 | Stop",
            content=content,
            color=color,
            fields=fields
        )

        if success:
            self.logger.info(f"Feishu Stop notification sent for session {session_id}")
        else:
            self.logger.warning(f"Failed to send Feishu Stop notification for session {session_id}")
