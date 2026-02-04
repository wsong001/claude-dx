#!/usr/bin/env python3
"""直接测试实际的Hook处理器."""
import json
import sys
from pathlib import Path

# 添加hooks目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from handlers.session_start import SessionStartHandler
from handlers.pre_tool_use import PreToolUseHandler
from handlers.post_tool_use import PostToolUseHandler


def test_session_start():
    """测试SessionStart事件."""
    print("\n" + "=" * 60)
    print("📍 测试 SessionStart Hook")
    print("=" * 60)

    handler = SessionStartHandler()

    # 模拟SessionStart的payload
    input_data = {
        "session_id": "test-session-12345678",
        "timestamp": "2026-02-05T01:00:00Z",
        "working_directory": "/Users/admin/Documents/GitHub/claude-dx"
    }

    handler.process(input_data)
    print("✅ SessionStart 通知已发送")


def test_pre_tool_use():
    """测试PreToolUse事件."""
    print("\n" + "=" * 60)
    print("🔧 测试 PreToolUse Hook")
    print("=" * 60)

    handler = PreToolUseHandler()

    # 模拟PreToolUse的payload
    input_data = {
        "session_id": "test-session-12345678",
        "timestamp": "2026-02-05T01:00:00Z",
        "tool_name": "Read",
        "tool_input": {
            "file_path": "/Users/admin/Documents/GitHub/claude-dx/hooks/common/feishu_bot.py"
        }
    }

    handler.process(input_data)
    print("✅ PreToolUse 通知已发送")


def test_post_tool_use_success():
    """测试PostToolUse成功事件."""
    print("\n" + "=" * 60)
    print("✅ 测试 PostToolUse Hook (成功)")
    print("=" * 60)

    handler = PostToolUseHandler()

    # 模拟PostToolUse成功的payload
    input_data = {
        "session_id": "test-session-12345678",
        "timestamp": "2026-02-05T01:00:00Z",
        "tool_name": "Edit",
        "tool_result": {
            "output": "File edited successfully: /Users/admin/Documents/GitHub/claude-dx/hooks/common/feishu_bot.py"
        },
        "duration": 125
    }

    handler.process(input_data)
    print("✅ PostToolUse (成功) 通知已发送")


def test_post_tool_use_failure():
    """测试PostToolUse失败事件."""
    print("\n" + "=" * 60)
    print("❌ 测试 PostToolUse Hook (失败)")
    print("=" * 60)

    handler = PostToolUseHandler()

    # 模拟PostToolUse失败的payload
    input_data = {
        "session_id": "test-session-12345678",
        "timestamp": "2026-02-05T01:00:00Z",
        "tool_name": "Bash",
        "tool_result": {
            "error": "Tests failed: 3 errors found",
            "exit_code": 1,
            "stderr": "Error: Test suite failed to run\nFailed tests: test/unit/api.test.js"
        },
        "duration": 2345
    }

    handler.process(input_data)
    print("✅ PostToolUse (失败) 通知已发送")


def main():
    """运行所有测试."""
    print("\n" + "=" * 60)
    print("🚀 Claude DX 飞书卡片消息 - 实际场景测试")
    print("=" * 60)

    try:
        # 执行所有测试
        test_session_start()
        test_pre_tool_use()
        test_post_tool_use_success()
        test_post_tool_use_failure()

        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有Hook场景测试完成")
        print("=" * 60)
        print("\n📱 请检查飞书客户端是否收到了以下卡片消息:")
        print("   1. 🔵 蓝色卡片 - SessionStart (会话开始)")
        print("   2. 🟠 橙色卡片 - PreToolUse (工具执行前)")
        print("   3. 🟢 绿色卡片 - PostToolUse 成功 (Edit工具)")
        print("   4. 🔴 红色卡片 - PostToolUse 失败 (Bash工具)")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
