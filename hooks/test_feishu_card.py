#!/usr/bin/env python3
"""测试飞书卡片消息发送功能."""
import json
import sys
from pathlib import Path

# 添加hooks目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from common.feishu_bot import FeishuAppBot
from common.logger import logger


def load_config():
    """从settings.local.json加载配置."""
    config_file = Path.home() / ".claude" / "settings.local.json"

    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return None

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 适配驼峰命名的配置格式
            return {
                "app_id": config.get("feishuAppId"),
                "app_secret": config.get("feishuAppSecret"),
                "receive_id": config.get("feishuReceiveId"),
                "receive_id_type": config.get("feishuReceiveIdType", "open_id")
            }
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None


def test_card_message():
    """测试发送卡片消息."""
    logger.info("=" * 60)
    logger.info("开始测试飞书卡片消息发送")
    logger.info("=" * 60)

    # 加载配置
    config = load_config()
    if not config:
        return False

    app_id = config.get("app_id")
    app_secret = config.get("app_secret")
    receive_id = config.get("receive_id")
    receive_id_type = config.get("receive_id_type", "open_id")

    if not all([app_id, app_secret, receive_id]):
        logger.error("Missing required config: app_id, app_secret, or receive_id")
        return False

    logger.info(f"配置信息:")
    logger.info(f"  App ID: {app_id[:8]}...")
    logger.info(f"  Receive ID: {receive_id[:8]}...")
    logger.info(f"  Receive ID Type: {receive_id_type}")

    # 创建Bot实例
    bot = FeishuAppBot(
        app_id=app_id,
        app_secret=app_secret,
        receive_id=receive_id,
        receive_id_type=receive_id_type
    )

    # 发送测试卡片
    logger.info("\n发送测试卡片消息...")
    success = bot.send_card_message(
        title="🧪 Claude DX 卡片消息测试",
        content="**修复验证测试**\n\n此消息用于验证卡片消息格式修复是否成功。",
        color="green",
        fields=[
            {
                "name": "修复内容",
                "value": "将 payload['card'] 改为 payload['content'] = json.dumps(card)"
            },
            {
                "name": "测试时间",
                "value": "2026-02-05"
            },
            {
                "name": "状态",
                "value": "✅ 如果你看到这条消息,说明修复成功!"
            }
        ]
    )

    if success:
        logger.info("✅ 卡片消息发送成功!")
        logger.info("请检查飞书客户端是否收到了格式正确的卡片消息")
        return True
    else:
        logger.error("❌ 卡片消息发送失败")
        logger.error("请检查日志中的错误信息")
        return False


if __name__ == "__main__":
    result = test_card_message()
    sys.exit(0 if result else 1)
