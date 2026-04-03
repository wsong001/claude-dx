#!/usr/bin/env python3
"""Notification hook 脚本 - 通用通知."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import (
    config, logger, FeishuAppBot, get_session_id
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
        project_dir = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "Unknown")

        # 根据级别选择颜色
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        color = color_map.get(level, "blue")

        if config.validate():
            bot = FeishuAppBot(
                app_id=config.app_id,
                app_secret=config.app_secret,
                receive_id=config.receive_id,
                receive_id_type=config.receive_id_type,
                cache_file=config.token_cache_file
            )

            content = f"项目: {project_dir}\n会话: {session_id}"
            if message:
                content += f"\n{message}"

            success = bot.send_card_message(
                title=f"通知 | {notification_type}",
                content=content,
                color=color,
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
