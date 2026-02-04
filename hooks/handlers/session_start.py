"""SessionStart Hook处理器."""
import os
from typing import Any, Dict
from handlers.base_handler import BaseHandler


class SessionStartHandler(BaseHandler):
    """会话开始处理器."""

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return "session_id" in input_data or "sessionId" in input_data

    def send_notification(self, input_data: Dict[str, Any]) -> None:
        """发送会话开始通知."""
        session_id = self.get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 获取工作目录
        cwd = input_data.get("cwd") or os.getcwd()

        # 检查是否在Git仓库中
        git_status = "Not a git repository"
        if input_data.get("git_repo"):
            branch = input_data.get("git_branch", "unknown")
            git_status = f"✓ Git repository (branch: {branch})"

        # 构建消息内容
        content = f"🚀 Claude Code 会话已启动"

        # 构建字段列表(添加图标)
        fields = [
            {
                "name": "会话ID",
                "value": f"`{session_id}`",
                "icon": "🎯"
            },
            {
                "name": "工作目录",
                "value": f"`{cwd}`",
                "icon": "📁"
            },
            {
                "name": "Git状态",
                "value": git_status,
                "icon": "🔀",
                "highlight": not input_data.get("git_repo")  # 非Git仓库时高亮提示
            },
            {
                "name": "启动时间",
                "value": timestamp,
                "icon": "⏰"
            },
        ]

        # 添加用户信息(如果有)
        if input_data.get("user"):
            fields.append({
                "name": "用户",
                "value": input_data["user"],
                "icon": "👤"
            })

        # 发送通知
        success = self.bot.send_card_message(
            title="🎯 会话开始 | Session Start",
            content=content,
            color="blue",
            fields=fields
        )

        if success:
            self.logger.info(f"SessionStart notification sent for session {session_id}")
        else:
            self.logger.warning(f"Failed to send SessionStart notification for session {session_id}")
