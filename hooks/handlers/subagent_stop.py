"""SubagentStop Hook处理器."""
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class SubagentStopHandler(BaseHandler):
    """子代理停止处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "agent_type" in input_data or "agent_name" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送子代理停止通知."""
        agent_type = input_data.get("agent_type", "unknown")
        agent_name = input_data.get("agent_name", agent_type)
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 判断完成状态
        status = input_data.get("status", "completed")
        is_success = status in ["completed", "success"]
        status_icon = "✅" if is_success else "⚠️"
        status_text = "成功完成" if is_success else f"已停止 ({status})"

        # 构建消息内容
        content = f"{status_icon} 子代理已停止\n\n**代理名称**: `{agent_name}`\n**代理类型**: `{agent_type}`\n**完成状态**: {status_text}\n**会话ID**: `{session_id}`"

        # 构建字段列表
        fields = []

        # 添加执行摘要
        if "summary" in input_data:
            summary = input_data["summary"]
            summary_text = self.filter_sensitive_info(summary, 300)
            fields.append({"name": "执行摘要", "value": summary_text})

        # 添加结果信息
        if "result" in input_data:
            result = input_data["result"]
            result_text = self.filter_sensitive_info(str(result), 300)
            fields.append({"name": "执行结果", "value": f"```\n{result_text}\n```"})

        # 添加统计信息
        stats = []
        if "turns" in input_data:
            stats.append(f"回合数: {input_data['turns']}")
        if "duration" in input_data:
            duration_sec = input_data["duration"] / 1000  # 转换为秒
            stats.append(f"耗时: {duration_sec:.2f}s")
        if "tokens_used" in input_data:
            stats.append(f"Token使用: {input_data['tokens_used']}")

        if stats:
            fields.append({"name": "统计信息", "value": " | ".join(stats)})

        fields.append({"name": "停止时间", "value": timestamp})

        # 发送通知
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
