#!/usr/bin/env python3
"""模拟Hook场景测试飞书卡片消息."""
import json
import sys
from pathlib import Path

# 添加hooks目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from handlers.base_handler import BaseHandler


class TestHandler(BaseHandler):
    """测试处理器."""

    def handle(self, payload: dict) -> dict:
        """处理测试事件."""
        test_type = payload.get("test_type", "session_start")

        if test_type == "session_start":
            return self._test_session_start(payload)
        elif test_type == "pre_tool_use":
            return self._test_pre_tool_use(payload)
        elif test_type == "post_tool_use":
            return self._test_post_tool_use(payload)
        else:
            return {"error": f"Unknown test type: {test_type}"}

    def _test_session_start(self, payload: dict) -> dict:
        """测试SessionStart事件."""
        self.notify_session_start(
            working_dir="/Users/admin/test-project",
            session_id="test-session-123"
        )
        return {"message": "SessionStart notification sent"}

    def _test_pre_tool_use(self, payload: dict) -> dict:
        """测试PreToolUse事件."""
        self.notify_pre_tool_use(
            tool_name="Read",
            parameters={"file_path": "/path/to/test.py"}
        )
        return {"message": "PreToolUse notification sent"}

    def _test_post_tool_use(self, payload: dict) -> dict:
        """测试PostToolUse事件."""
        # 测试成功场景
        self.notify_post_tool_use(
            tool_name="Edit",
            parameters={"file_path": "/path/to/test.py"},
            success=True,
            result="File edited successfully"
        )

        # 测试失败场景
        self.notify_post_tool_use(
            tool_name="Bash",
            parameters={"command": "npm test"},
            success=False,
            error="Tests failed: 3 errors"
        )

        return {"message": "PostToolUse notifications sent (success + failure)"}


def main():
    """运行测试."""
    print("=" * 60)
    print("测试 Hook 场景的飞书卡片消息")
    print("=" * 60)

    handler = TestHandler()

    # 测试场景
    test_scenarios = [
        {
            "name": "📍 SessionStart",
            "test_type": "session_start"
        },
        {
            "name": "🔧 PreToolUse",
            "test_type": "pre_tool_use"
        },
        {
            "name": "✅ PostToolUse (成功 + 失败)",
            "test_type": "post_tool_use"
        }
    ]

    for scenario in test_scenarios:
        print(f"\n{scenario['name']} 测试...")
        result = handler.handle(scenario)
        print(f"  结果: {result.get('message', result)}")

    print("\n" + "=" * 60)
    print("✅ 所有测试场景已执行")
    print("📱 请检查飞书客户端是否收到了 3 条卡片消息:")
    print("   1. 蓝色卡片 - SessionStart")
    print("   2. 橙色卡片 - PreToolUse")
    print("   3. 绿色卡片 - PostToolUse (成功)")
    print("   4. 红色卡片 - PostToolUse (失败)")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 测试失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
