"""Notification Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class NotificationHandler(BaseHandler):
    """通知处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "notification_type" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送通知通知."""
        notification_type = input_data.get("notification_type", "unknown")
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")
        message = input_data.get("message", "")

        # 根据通知类型设置颜色和标题
        type_config = self._get_type_config(notification_type)

        # 构建消息内容
        content = f"{type_config['icon']} {type_config['description']}"
        if message:
            content += f"\n💬 {message}"

        # 构建字段列表(添加图标和高亮)
        fields = [
            {
                "name": "会话ID",
                "value": f"`{session_id}`",
                "icon": "🎯"
            },
            {
                "name": "通知类型",
                "value": notification_type,
                "icon": "🏷️",
                "highlight": notification_type == "permission_prompt"  # 权限请求高亮
            },
            {
                "name": "触发时间",
                "value": timestamp,
                "icon": "⏰"
            },
        ]

        # 添加额外信息(如果有)
        if input_data.get("details"):
            details = self.format_dict_summary(input_data["details"], 200)
            fields.append({
                "name": "详细信息",
                "value": f"```\n{details}\n```",
                "icon": "📄"
            })

        # 发送通知
        success = self.bot.send_card_message(
            title=f"{type_config['icon']} {type_config['title']}",
            content=content,
            color=type_config['color'],
            fields=fields
        )

        if success:
            self.logger.info(f"Notification sent for type {notification_type}")
        else:
            self.logger.warning(f"Failed to send Notification for type {notification_type}")

    def _get_type_config(self, notification_type: str) -> Dict[str, str]:
        """
        获取通知类型配置.

        Args:
            notification_type: 通知类型

        Returns:
            Dict: 配置字典
        """
        type_configs = {
            "permission_prompt": {
                "icon": "🔐",
                "title": "权限请求 | Permission Prompt",
                "description": "Claude 需要权限批准",
                "color": "yellow"
            },
            "idle_prompt": {
                "icon": "💤",
                "title": "空闲提示 | Idle Prompt",
                "description": "Claude 已闲置等待输入",
                "color": "blue"
            },
            "auth_success": {
                "icon": "✅",
                "title": "认证成功 | Auth Success",
                "description": "用户认证成功",
                "color": "green"
            },
            "elicitation_dialog": {
                "icon": "❓",
                "title": "需要输入 | Elicitation Dialog",
                "description": "系统需要用户提供信息",
                "color": "orange"
            }
        }

        # 默认配置
        return type_configs.get(notification_type, {
            "icon": "🔔",
            "title": "系统通知 | Notification",
            "description": "Claude Code 通知",
            "color": "blue"
        })
