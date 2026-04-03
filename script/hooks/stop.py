#!/usr/bin/env python3
"""Stop hook 脚本 - 会话结束通知."""
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

        # 提取数据
        stop_reason = input_data.get("stop_reason", "Unknown")
        session_id = get_session_id(input_data)
        project_dir = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "Unknown")

        # 格式化停止原因
        reason_map = {
            "user_requested": "用户主动结束",
            "error": "发生错误",
            "timeout": "超时",
            "interrupted": "被中断",
            "completed": "正常完成",
        }
        reason_text = reason_map.get(stop_reason, stop_reason)

        if config.validate():
            bot = FeishuAppBot(
                app_id=config.app_id,
                app_secret=config.app_secret,
                receive_id=config.receive_id,
                receive_id_type=config.receive_id_type,
                cache_file=config.token_cache_file
            )

            content = f"项目: {project_dir}\n会话: {session_id} | {reason_text}"

            success = bot.send_card_message(
                title="会话结束",
                content=content,
                color="grey",
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
