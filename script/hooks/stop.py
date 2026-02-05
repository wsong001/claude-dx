#!/usr/bin/env python3
"""Stop hook 脚本 - 会话结束通知."""
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

        # 提取数据
        stop_reason = input_data.get("stop_reason", "Unknown")
        session_id = get_session_id(input_data)
        timestamp = input_data.get("timestamp", "N/A")

        # 格式化停止原因
        reason_map = {
            "user_requested": "用户主动结束",
            "error": "发生错误",
            "timeout": "超时",
            "interrupted": "被中断",
            "completed": "正常完成",
        }
        reason_text = reason_map.get(stop_reason, stop_reason)

        if config.is_system_notification():
            # 系统通知
            content = f"会话结束: {reason_text}"
            send_system_notification(title="🔚 Claude Code", message=content)
            logger.info(f"System notification sent for Stop: {reason_text}")

        elif config.validate():
            # 飞书通知
            content = f"**会话结束**\n\n原因: {reason_text}"

            fields = [
                {"name": "会话ID", "value": f"`{session_id}`", "icon": "🎯"},
                {"name": "结束原因", "value": reason_text, "icon": "🔚"},
                {"name": "结束时间", "value": timestamp, "icon": "⏰"},
            ]

            bot = FeishuAppBot(
                app_id=config.app_id,
                app_secret=config.app_secret,
                receive_id=config.receive_id,
                receive_id_type=config.receive_id_type,
                cache_file=config.token_cache_file
            )

            success = bot.send_card_message(
                title="🔚 会话结束",
                content=content,
                color="gray",
                fields=fields
            )

            if success:
                logger.info(f"Feishu notification sent for Stop: {reason_text}")
            else:
                logger.warning(f"Failed to send Feishu notification for Stop: {reason_text}")

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
