#!/usr/bin/env python3
"""PermissionRequest hook 脚本 - 权限请求通知."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib import (
    config, logger, FeishuAppBot,
    get_session_id, filter_sensitive_info
)


def main():
    """主函数."""
    try:
        # 从 stdin 读取输入
        input_data = json.load(sys.stdin)

        # 验证输入
        if "permission_type" not in input_data:
            logger.error("Invalid input: missing permission_type")
            json.dump(input_data, sys.stdout)
            sys.stdout.flush()
            return

        # 提取数据
        permission_type = input_data.get("permission_type", "Unknown")
        permission_data = input_data.get("permission_data", {})
        session_id = get_session_id(input_data)
        project_dir = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "Unknown")

        # 构建权限描述
        permission_desc = _format_permission_description(permission_type, permission_data)

        if config.validate():
            bot = FeishuAppBot(
                app_id=config.app_id,
                app_secret=config.app_secret,
                receive_id=config.receive_id,
                receive_id_type=config.receive_id_type,
                cache_file=config.token_cache_file
            )

            content = f"项目: {project_dir}\n会话: {session_id}\n{permission_desc}"

            success = bot.send_card_message(
                title="权限请求",
                content=content,
                color="yellow",
            )

            if success:
                logger.info(f"Feishu notification sent for PermissionRequest: {permission_type}")
            else:
                logger.warning(f"Failed to send Feishu notification for PermissionRequest: {permission_type}")

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


def _format_permission_description(permission_type: str, permission_data: dict) -> str:
    """格式化权限描述."""
    descriptions = {
        "dangerouslyDisableSandbox": "禁用沙箱模式",
        "autoApprove": "自动批准权限",
        "bypassConfirmation": "跳过确认",
        "executeCommand": "执行命令",
        "writeFile": "写入文件",
        "networkAccess": "网络访问",
    }

    desc = descriptions.get(permission_type, permission_type)

    if "reason" in permission_data:
        desc += f"\n原因: {permission_data['reason']}"

    return desc


if __name__ == "__main__":
    main()
