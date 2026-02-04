"""PermissionRequest Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class PermissionRequestHandler(BaseHandler):
    """权限请求处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "permission_type" in input_data or "tool_name" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送权限请求通知."""
        permission_type = input_data.get("permission_type", "unknown")
        tool_name = input_data.get("tool_name", "Unknown")
        resource = input_data.get("resource", "")
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 构建消息内容
        content = f"🔐 需要用户审批\n\n**权限类型**: `{permission_type}`\n**工具名称**: `{tool_name}`\n**会话ID**: `{session_id}`"

        # 构建字段列表
        fields = []

        # 添加资源信息
        if resource:
            resource_summary = self.filter_sensitive_info(resource, 200)
            fields.append({"name": "请求资源", "value": f"`{resource_summary}`"})

        # 添加操作信息
        if "action" in input_data:
            action = input_data["action"]
            fields.append({"name": "请求操作", "value": action})

        # 添加描述信息
        if "description" in input_data:
            description = input_data["description"]
            fields.append({"name": "说明", "value": description})

        fields.append({"name": "请求时间", "value": timestamp})

        # 添加提示
        fields.append({
            "name": "⚠️ 注意",
            "value": "请在Claude Code中审批此权限请求"
        })

        # 发送通知
        success = self.bot.send_card_message(
            title="🔒 权限请求 | Permission Request",
            content=content,
            color="yellow",
            fields=fields
        )

        if success:
            self.logger.info(f"PermissionRequest notification sent for {permission_type}")
        else:
            self.logger.warning(f"Failed to send PermissionRequest notification for {permission_type}")
