#!/usr/bin/env python3
"""测试新增的 Notification 和 Stop hooks."""
import json
import sys
from pathlib import Path

# 添加hooks目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from handlers.notification import NotificationHandler
from handlers.stop import StopHandler


def test_notification_hooks():
    """测试所有 Notification 类型."""
    print("\n" + "=" * 60)
    print("📬 测试 Notification Hook")
    print("=" * 60)

    handler = NotificationHandler()

    # 测试不同的通知类型
    notification_types = [
        {
            "type": "permission_prompt",
            "message": "需要执行 git push 命令的权限"
        },
        {
            "type": "idle_prompt",
            "message": "等待用户下一步指令"
        },
        {
            "type": "auth_success",
            "message": "GitHub 认证成功"
        },
        {
            "type": "elicitation_dialog",
            "message": "请选择要使用的数据库"
        }
    ]

    for idx, notification in enumerate(notification_types, 1):
        print(f"\n{idx}. 测试 {notification['type']} 通知...")

        input_data = {
            "session_id": "test-session-12345678",
            "timestamp": "2026-02-05T01:30:00Z",
            "notification_type": notification["type"],
            "message": notification["message"]
        }

        handler.process(input_data)
        print(f"   ✅ {notification['type']} 通知已发送")


def test_stop_hooks():
    """测试 Stop Hook 的不同场景."""
    print("\n" + "=" * 60)
    print("🏁 测试 Stop Hook")
    print("=" * 60)

    handler = StopHandler()

    # 测试场景
    scenarios = [
        {
            "name": "正常完成",
            "data": {
                "session_id": "test-session-12345678",
                "timestamp": "2026-02-05T01:30:00Z",
                "reason": "任务完成",
                "stop_type": "normal",
                "stats": {
                    "turns": 5,
                    "tokens": 1234,
                    "duration": 3500
                }
            }
        },
        {
            "name": "用户中断",
            "data": {
                "session_id": "test-session-12345678",
                "timestamp": "2026-02-05T01:30:00Z",
                "reason": "用户按下 Ctrl+C",
                "stop_type": "interrupted",
                "stats": {
                    "turns": 2,
                    "tokens": 567
                }
            }
        },
        {
            "name": "异常停止",
            "data": {
                "session_id": "test-session-12345678",
                "timestamp": "2026-02-05T01:30:00Z",
                "reason": "系统错误",
                "stop_type": "error",
                "error": "Network timeout: Failed to connect to API server"
            }
        }
    ]

    for idx, scenario in enumerate(scenarios, 1):
        print(f"\n{idx}. 测试 {scenario['name']}...")
        handler.process(scenario["data"])
        print(f"   ✅ {scenario['name']} 通知已发送")


def main():
    """运行所有测试."""
    print("\n" + "=" * 60)
    print("🚀 Claude DX 新增 Hooks 测试")
    print("=" * 60)

    try:
        # 测试 Notification hooks
        test_notification_hooks()

        # 测试 Stop hooks
        test_stop_hooks()

        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        print("\n📱 请检查飞书客户端是否收到以下卡片消息:")
        print("\n【Notification 通知】")
        print("   1. 🔐 黄色卡片 - permission_prompt (权限请求)")
        print("   2. 💤 蓝色卡片 - idle_prompt (空闲提示)")
        print("   3. ✅ 绿色卡片 - auth_success (认证成功)")
        print("   4. ❓ 橙色卡片 - elicitation_dialog (需要输入)")
        print("\n【Stop 通知】")
        print("   5. ✅ 绿色卡片 - 正常完成")
        print("   6. ⏸️ 黄色卡片 - 用户中断")
        print("   7. ❌ 红色卡片 - 异常停止")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
