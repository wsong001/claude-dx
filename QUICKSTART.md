# Claude DX 快速启动指南

## 10分钟快速开始

### 步骤1: 创建飞书应用 (5分钟)

#### 1.1 创建应用

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用信息:
   - 应用名称: "Claude DX通知机器人"
   - 应用描述: "Claude Code实时通知助手"
4. 点击"创建"

#### 1.2 获取凭证

在应用详情页 → "凭证与基础信息":
- **App ID**: 复制保存 (格式: `cli_xxxxxxxxxxxxxx`)
- **App Secret**: 点击"查看" → 复制保存

#### 1.3 申请权限

在应用详情页 → "权限管理":
1. 搜索并申请以下权限:
   - ✅ `im:message` (获取与发送单聊、群组消息)
   - ✅ `im:message:send_as_bot` (以应用的身份发消息)
2. 点击"申请权限"
3. 等待管理员审核通过(或自行审核,如果你是管理员)

#### 1.4 获取接收者ID

**方式A: 发送给个人**
1. 飞书管理后台 → 通讯录 → 找到你的账号
2. 查看用户详情,复制 `open_id` (格式: `ou_xxxxxxxxxx`)

**方式B: 发送到群聊**
1. 创建或打开一个群聊
2. 群设置 → 群机器人 → 添加机器人
3. 搜索你的应用名称 → 添加
4. 获取 `chat_id` (可通过API或事件获取,格式: `oc_xxxxxxxxxx`)

### 步骤2: 配置应用机器人 (2分钟)

#### 方式A: 使用 `/Setup` 命令（推荐）

```bash
cd /Users/admin/Documents/GitHub/claude-dx
claude --plugin-dir ./
# 在 Claude Code 中运行
/Setup
```

按向导提示输入配置信息，向导会自动保存到 `~/.claude/settings.local.json`。

#### 方式B: 手动配置

创建或编辑 `~/.claude/settings.local.json`:

```bash
mkdir -p ~/.claude
cat > ~/.claude/settings.local.json << 'EOF'
{
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
EOF
```

**配置说明:**
- `feishuReceiveIdType`:
  - 使用 `"open_id"` 发送给个人
  - 使用 `"chat_id"` 发送到群聊

### 步骤3: 测试通知 (2分钟)

```bash
cd /Users/admin/Documents/GitHub/claude-dx

# 测试1: 验证配置
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config

print(f"✅ App ID: {config.app_id[:10]}..." if config.app_id else "❌ App ID未配置")
print(f"✅ Receive ID: {config.receive_id}" if config.receive_id else "❌ Receive ID未配置")
print(f"✅ 配置有效" if config.validate() else "❌ 配置无效")
EOF

# 测试2: 获取Token
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config
from common.feishu_bot import FeishuTokenManager
from pathlib import Path

tm = FeishuTokenManager(config.app_id, config.app_secret, Path.home() / ".feishu_token_cache")
try:
    token = tm.get_token()
    print(f"✅ Token获取成功: {token[:20]}...")
except Exception as e:
    print(f"❌ Token获取失败: {e}")
EOF

# 测试3: 发送测试消息
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config
from common.feishu_bot import FeishuAppBot

bot = FeishuAppBot(
    config.app_id,
    config.app_secret,
    config.receive_id,
    config.receive_id_type
)

success = bot.send_card_message(
    title='✅ 测试成功 | Test Success',
    content='Claude DX应用机器人已正确配置!',
    color='green',
    fields=[{'name': '状态', 'value': '插件工作正常'}]
)

print('✅ 消息已发送到飞书!' if success else '❌ 发送失败,请检查配置')
EOF
```

如果看到飞书收到测试消息,说明配置成功!

### 步骤4: 启动Claude Code (1分钟)

```bash
# 方式1: 直接加载插件
cd /Users/admin/Documents/GitHub/claude-dx
claude --plugin-dir ./

# 方式2: 全局安装(推荐)
mkdir -p ~/.claude/plugins
ln -s /Users/admin/Documents/GitHub/claude-dx ~/.claude/plugins/claude-dx
claude
```

### 完成!

现在,当你使用Claude Code时:
- 🎯 会话启动时会收到通知
- ⚙️ 工具执行前会收到通知
- ✓ 工具执行完成后会收到通知
- 🔒 权限请求时会收到通知
- 🤖 子代理完成时会收到通知

## 故障排查

### 问题1: Token获取失败

**原因**: App ID 或 App Secret 错误

**解决方案:**
```bash
# 检查配置
python3 -c "
import sys
sys.path.insert(0, 'hooks')
from common.config import config
print(f'App ID: {config.app_id}')
print(f'App Secret configured: {bool(config.app_secret)}')
"
```

### 问题2: 权限不足

**原因**: 应用权限未通过审核

**解决方案:**
1. 访问飞书开放平台 → 应用详情 → 权限管理
2. 检查权限状态:
   - ✅ `im:message` - 必须是"已通过"
   - ✅ `im:message:send_as_bot` - 必须是"已通过"
3. 如果是"待审核",联系管理员审核
4. 如果是"已拒绝",重新申请并说明用途

### 问题3: 找不到接收者

**原因**: Receive ID 错误或类型不匹配

**解决方案:**
```bash
# 检查配置
python3 -c "
import sys
sys.path.insert(0, 'hooks')
from common.config import config
print(f'Receive ID: {config.receive_id}')
print(f'Receive ID Type: {config.receive_id_type}')
"
```

- 如果发送给用户: 使用 `open_id` (格式: `ou_xxx`)
- 如果发送到群聊: 使用 `chat_id` (格式: `oc_xxx`)

### 问题4: Python依赖缺失

```bash
cd /Users/admin/Documents/GitHub/claude-dx/hooks
pip3 install --break-system-packages -r requirements.txt
```

### 问题5: Hook执行错误

**查看错误日志:**
```bash
# Hook的错误会输出到stderr,可以在Claude Code的日志中查看
# 或者单独测试Hook:
echo '{"session_id":"test"}' | python3 hooks/entry_points/session_start_hook.py 2>&1
```

## 下一步

- 查看 [README.md](README.md) 了解完整功能和详细测试
- 查看 [hooks/README.md](hooks/README.md) 了解开发文档
- 自定义消息格式 - 编辑 `hooks/handlers/` 目录下的处理器

## 需要帮助?

- 提交Issue: https://github.com/yourusername/claude-dx/issues
- 查看文档: [README.md](README.md)
- 飞书开放平台文档: https://open.feishu.cn/document/

---

**祝你使用愉快!** 🚀
