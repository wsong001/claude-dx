"""Notification Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class NotificationHandler(BaseHandler):
    """通知处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "notification_type" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送通知."""
        notification_type = input_data.get("notification_type", "unknown")
        timestamp = input_data.get("timestamp", "N/A")
        message = input_data.get("message", "")

        # 根据通知类型获取图标和描述
        type_config = self._get_type_config(notification_type)

        # 根据通知模式选择发送方式
        if self.config.is_system_notification():
            self._send_system_notification(notification_type, type_config, message)
        elif self.bot:
            self._send_feishu_notification(input_data, notification_type, type_config, message, timestamp)

    def _send_system_notification(self, notification_type: str, type_config: Dict[str, str], message: str) -> None:
        """发送系统通知."""
        title = f"{type_config['icon']} {type_config['title']}"
        content = type_config['description']
        if message:
            content += f"\n{message}"

        success = self.send_system_notification(title, content)

        if success:
            self.logger.info(f"System notification sent for type {notification_type}")
        else:
            self.logger.warning(f"Failed to send system notification for type {notification_type}")

    def _send_feishu_notification(
        self,
        input_data: Dict[str, Any],
        notification_type: str,
        type_config: Dict[str, str],
        message: str,
        timestamp: str
    ) -> None:
        """发送飞书通知."""
        session_id = self.get_session_id(input_data)

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
            self.logger.info(f"Feishu notification sent for type {notification_type}")
        else:
            self.logger.warning(f"Failed to send Feishu notification for type {notification_type}")

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
