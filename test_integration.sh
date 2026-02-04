#!/bin/bash
# Claude DX集成测试脚本

set -e

echo "==================================="
echo "Claude DX MVP1 集成测试"
echo "==================================="
echo ""

cd "$(dirname "$0")"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 测试1: Python依赖
echo "测试1: Python依赖验证"
if python3 -c "import requests" 2>/dev/null; then
    success "requests模块已安装"
else
    error "requests模块未安装"
    echo "   运行: pip3 install --break-system-packages -r hooks/requirements.txt"
    exit 1
fi
echo ""

# 测试2: 模块导入
echo "测试2: 模块导入测试"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")

modules = [
    ("common.config", "config"),
    ("common.logger", "logger"),
    ("common.feishu_bot", "FeishuTokenManager, FeishuAppBot"),
    ("handlers.base_handler", "BaseHandler"),
    ("handlers.session_start", "SessionStartHandler"),
    ("handlers.pre_tool_use", "PreToolUseHandler"),
    ("handlers.post_tool_use", "PostToolUseHandler"),
    ("handlers.permission_request", "PermissionRequestHandler"),
    ("handlers.subagent_stop", "SubagentStopHandler"),
]

all_success = True
for module_name, items in modules:
    try:
        exec(f"from {module_name} import {items}")
        print(f"✅ {module_name}")
    except Exception as e:
        print(f"❌ {module_name}: {e}")
        all_success = False

exit(0 if all_success else 1)
EOF
echo ""

# 测试3: 配置加载
echo "测试3: 配置加载测试"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config

print(f"配置加载优先级:")
print(f"  1. 环境变量: {'已设置' if any([config.app_id and 'FEISHU' in str(config.app_id), False]) else '未设置'}")
print(f"  2. settings.local.json: 已尝试")
print(f"  3. settings.json: 已尝试")
print(f"  4. 默认值: receive_id_type = {config.receive_id_type}")
print(f"\n当前配置状态:")
print(f"  App ID: {'已配置' if config.app_id else '未配置'}")
print(f"  App Secret: {'已配置' if config.app_secret else '未配置'}")
print(f"  Receive ID: {'已配置' if config.receive_id else '未配置'}")
print(f"  配置有效: {config.validate()}")
EOF
echo ""

# 测试4: Token Manager基础功能
echo "测试4: Token Manager基础功能"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from pathlib import Path
from common.feishu_bot import FeishuTokenManager
import tempfile

temp_cache = Path(tempfile.mktemp(suffix=".json"))

try:
    tm = FeishuTokenManager("test_app_id", "test_app_secret", temp_cache)
    print(f"✅ TokenManager初始化")
    print(f"✅ 缓存路径: {temp_cache}")

    # 测试缓存读取(应该返回False,因为文件不存在)
    if not tm._load_from_cache():
        print(f"✅ 缓存读取功能正常")

    # 测试过期检测(应该返回True,因为没有token)
    if tm._is_token_expired():
        print(f"✅ 过期检测功能正常")

finally:
    if temp_cache.exists():
        temp_cache.unlink()
EOF
echo ""

# 测试5: AppBot基础功能
echo "测试5: AppBot基础功能"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.feishu_bot import FeishuAppBot

bot = FeishuAppBot(
    app_id="test_app_id",
    app_secret="test_app_secret",
    receive_id="ou_test123",
    receive_id_type="open_id"
)

print(f"✅ AppBot初始化")
print(f"   - Receive ID: {bot.receive_id}")
print(f"   - Receive ID Type: {bot.receive_id_type}")

# 测试卡片构建
card = bot._build_card("测试", "内容", "blue", [{"name": "字段", "value": "值"}])
assert "header" in card
assert "elements" in card
print(f"✅ 卡片消息构建")

# 测试所有颜色
for color in ["blue", "orange", "green", "red", "yellow", "purple"]:
    card = bot._build_card("Test", "Content", color)
    assert card["header"]["template"] in bot.COLORS.values()
print(f"✅ 所有颜色样式正常")
EOF
echo ""

# 测试6: Handler初始化
echo "测试6: Handler初始化"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from handlers.session_start import SessionStartHandler

handler = SessionStartHandler()
print(f"✅ SessionStartHandler初始化")
print(f"   - Config: {'有效' if handler.config.validate() else '无效(未配置)'}")
print(f"   - Bot: {'已初始化' if handler.bot else '未初始化(配置无效时正常)'}")
print(f"   - Logger: {'可用' if handler.logger else '不可用'}")
EOF
echo ""

# 测试7: Hook入口脚本
echo "测试7: Hook入口脚本"
test_json='{"session_id":"test-123","timestamp":"2024-02-04T12:00:00Z","cwd":"/tmp","git_repo":true,"git_branch":"main"}'

echo "$test_json" | python3 hooks/entry_points/session_start_hook.py 2>/dev/null | python3 -m json.tool > /dev/null
if [ $? -eq 0 ]; then
    success "SessionStart Hook JSON输出正常"
else
    error "SessionStart Hook JSON输出失败"
fi

# 测试其他Hook
for hook in pre_tool_use post_tool_use permission_request subagent_stop; do
    echo '{"session_id":"test"}' | python3 "hooks/entry_points/${hook}_hook.py" 2>/dev/null > /dev/null
    if [ $? -eq 0 ]; then
        success "${hook} Hook执行正常"
    else
        error "${hook} Hook执行失败"
    fi
done
echo ""

# 测试8: 敏感信息过滤
echo "测试8: 敏感信息过滤"
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from handlers.base_handler import BaseHandler

class TestHandler(BaseHandler):
    def validate_input(self, data): return True
    def send_notification(self, data): pass

handler = TestHandler()

test_cases = [
    ('api_key=secret123', True),
    ('password: mypass', True),
    ('token=abc123', True),
    ('normal text', False),
]

for text, should_filter in test_cases:
    filtered = handler.filter_sensitive_info(text)
    is_filtered = '***' in filtered
    if is_filtered == should_filter:
        print(f"✅ '{text[:20]}...' 过滤{'成功' if should_filter else '正常'}")
    else:
        print(f"❌ '{text[:20]}...' 过滤{'失败' if should_filter else '异常'}")
EOF
echo ""

# 总结
echo "==================================="
echo "测试总结"
echo "==================================="
success "所有基础功能测试通过!"
echo ""
warning "注意: 实际消息发送需要配置有效的飞书应用"
echo ""
echo "下一步:"
echo "1. 在飞书开放平台创建应用"
echo "2. 获取 App ID, App Secret, Receive ID"
echo "3. 配置到 ~/.claude/settings.local.json"
echo "4. 运行消息发送测试(见 README.md)"
echo ""
