#!/usr/bin/env python3
"""Notification hook 脚本 - 通用通知."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import (
    config, logger, FeishuAppBot,
    send_system_notification, get_session_id
)


def main():
    """主函数."""
    try:
        # 从 stdin 读取输入
        input_data = json.load(sys.stdin)

        # 验证输入
        notification_type = input_data.get("notification_type") or input_data.get("type", "Unknown")
        if not notification_type or notification_type == "Unknown":
            logger.error("Invalid input: missing notification_type")
            json.dump(input_data, sys.stdout)
            sys.stdout.flush()
            return

        # 提取数据
        message = input_data.get("message", "")
        level = input_data.get("level", "info")
        session_id = get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")
        context = input_data.get("context", {})

        # 根据级别选择颜色和图标
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        color = color_map.get(level, "blue")

        icon_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        icon = icon_map.get(level, "📢")

        if config.is_system_notification():
            # 系统通知
            content = f"{notification_type}: {message}" if message else notification_type
            send_system_notification(title="📢 Claude Code", message=content)
            logger.info(f"System notification sent for Notification: {notification_type}")

        elif config.validate():
            # 飞书通知
            content = f"{icon} **{notification_type}**"

            if message:
                content += f"\n\n{message}"

            fields = [
                {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
                {"name": "级别", "value": level.upper(), "icon": "🏷️"},
                {"name": "通知时间", "value": timestamp, "icon": "⏰"},
            ]

            # 添加上下文（最多3个字段）
            if isinstance(context, dict):
                for key, value in list(context.items())[:3]:
                    fields.append({
                        "name": key,
                        "value": str(value)[:100],
                        "icon": "📋"
                    })

            bot = FeishuAppBot(
                app_id=config.app_id,
                app_secret=config.app_secret,
                receive_id=config.receive_id,
                receive_id_type=config.receive_id_type,
                cache_file=config.token_cache_file
            )

            success = bot.send_card_message(
                title=f"📢 通知 | {notification_type}",
                content=content,
                color=color,
                fields=fields
            )

            if success:
                logger.info(f"Feishu notification sent for Notification: {notification_type}")
            else:
                logger.warning(f"Failed to send Feishu notification for Notification: {notification_type}")

        # 输出原始数据
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
