# Claude DX

Claude Code 插件，用于飞书/系统消息通知。

## 功能特性

### MVP1 - Hooks 消息通知

通过 Hooks 在 Claude Code 运行时发送实时消息通知：

- 🎯 **SessionStart** - 会话开始时通知
- ⚙️ **PreToolUse** - 工具执行前通知
- ✓ **PostToolUse** - 工具执行后通知
- 🔒 **PermissionRequest** - 权限请求时通知
- 🤖 **SubagentStop** - 子代理停止时通知

### 通知方式

#### 系统通知（推荐用于本地开发）
- ✅ 无需配置，开箱即用
- ✅ macOS 右上角原生通知
- ✅ 无网络依赖
- ✅ 适合个人本地开发

#### 飞书应用机器人（推荐用于远程通知）
- ✅ 支持远程通知
- ✅ 支持富文本卡片消息
- ✅ 适合团队协作
- ⚠️ 需要配置飞书应用

### 特性

- ✅ 详细模式 - 包含完整上下文信息
- ✅ 敏感信息过滤 - 自动过滤 API keys、tokens、passwords 等
- ✅ 彩色卡片消息 - 不同 Hook 类型使用不同颜色
- ✅ 错误隔离 - 通知失败不影响 Claude 执行
- ✅ 重试机制 - 自动处理 API 限流

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/claude-dx.git
cd claude-dx
```

### 2. 安装 Python 依赖

```bash
cd hooks
pip3 install -r requirements.txt
```

### 3. 配置应用机器人

#### 方式 A: 使用 `/setup` 命令（推荐）

安装插件后，使用交互式配置向导：

```bash
# 1. 启动 Claude Code（指定插件目录）
claude --plugin-dir /path/to/claude-dx

# 2. 在 Claude Code 中运行
/setup
```

配置向导会引导你完成：
1. 选择通知方式（系统通知 or 飞书应用机器人）
2. 如果选择飞书，输入相关配置
3. 自动验证并保存配置

#### 方式 B: 手动配置

**系统通知（无需配置）**

默认使用系统通知，无需任何配置。

**飞书应用机器人**

在 `~/.claude/settings.local.json` 中添加配置：

```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

**配置说明:**
- `notificationType`: 通知类型（"system" 或 "feishu"）
- `feishuAppId`: 飞书应用 ID
- `feishuAppSecret`: 飞书应用密钥
- `feishuReceiveId`: 接收者 ID (用户的 open_id 或群聊的 chat_id)
- `feishuReceiveIdType`: 接收者类型
  - `open_id` - 发送给用户(推荐用于个人通知)
  - `chat_id` - 发送到群聊(推荐用于团队协作)

如果 `settings.local.json` 不存在，创建它：

```bash
mkdir -p ~/.claude
cat > ~/.claude/settings.local.json << 'EOF'
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
EOF
```

### 4. 创建飞书应用（仅飞书通知需要）

#### 4.1 创建飞书应用

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用名称和描述(如: "Claude DX通知机器人")
4. 创建完成后，进入应用详情页面

#### 4.2 获取 App ID 和 App Secret

在"凭证与基础信息"页面:
- **App ID**: 直接可见，格式为 `cli_xxxxxxxxxxxxxx`
- **App Secret**: 点击"查看"按钮获取

#### 4.3 配置应用权限

在"权限管理"页面，申请以下权限(需管理员审核):
- ✅ `im:message` - 获取与发送单聊、群组消息
- ✅ `im:message:send_as_bot` - 以应用的身份发消息

配置后等待管理员审核通过。

#### 4.4 获取接收者 ID

**方式1: 发送给用户(个人通知)**

获取用户的 `open_id`:
- 方法A: 飞书管理后台 → 通讯录 → 找到用户 → 查看详情 → 复制 open_id
- 方法B: 让用户给机器人发消息，在事件回调中获取 sender_id

**方式2: 发送到群聊(团队协作)**

获取群聊的 `chat_id`:
1. 创建群聊或使用现有群聊
2. 群设置 → 群机器人 → 添加机器人 → 搜索你的应用名称并添加
3. 通过 API 获取群组列表，或在群消息事件中获取 chat_id

### 5. 加载插件

启动 Claude Code 时加载插件：

```bash
# 方式1: 使用 --plugin-dir 参数
cd /Users/admin/Documents/GitHub/claude-dx
claude --plugin-dir ./

# 方式2: 将插件链接到全局插件目录
mkdir -p ~/.claude/plugins
ln -s /Users/admin/Documents/GitHub/claude-dx ~/.claude/plugins/claude-dx
claude
```

## 使用

加载插件后，Claude Code 会自动在以下情况发送通知：

1. **会话开始** - 显示会话 ID、工作目录、Git 状态
2. **工具执行前** - 显示工具名称和输入参数摘要
3. **工具执行后** - 显示执行状态和输出摘要
4. **权限请求** - 提示需要用户审批
5. **子代理停止** - 显示代理执行摘要和统计信息

## 命令

Commands 使用纯 Markdown 文件实现，由 Claude Code 解释执行。

### `/setup` - 配置向导

交互式配置通知功能。

**用法**: 在 Claude Code 中运行 `/setup`

**实现**: `commands/setup.md`（纯 Markdown，无需 Python 脚本）

**配置内容**:
- 通知方式：系统通知 or 飞书应用机器人
- 飞书 App ID: 从飞书开发者后台获取
- 飞书 App Secret: 应用密钥
- 接收者 ID: 用户 open_id 或群聊 chat_id
- 接收者类型: open_id（个人）或 chat_id（群聊）

**配置位置**: `~/.claude/settings.local.json`

**验证**: 自动测试 API 连接，确保配置正确。

## 本地测试

### 测试1: Python 依赖验证

```bash
cd hooks
python3 -c "import requests; print('✓ requests installed')"
```

### 测试2: 系统通知测试

```bash
# 先配置为系统通知
echo '{"notificationType":"system"}' > ~/.claude/settings.local.json

# 测试 SessionStart hook
echo '{"session_id":"test-123","timestamp":"2024-02-05T12:00:00Z","cwd":"/tmp"}' | \
  python3 ../script/hooks/session_start.py
```

预期结果：右上角弹出系统通知

### 测试3: 配置验证

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "../script/hooks")
from common.config import config

print(f"Notification Type: {config.notification_type}")
if config.is_feishu_notification():
    print(f"App ID: {config.app_id[:10]}..." if config.app_id else "App ID: Not configured")
    print(f"App Secret: {config.app_secret[:10]}..." if config.app_secret else "App Secret: Not configured")
    print(f"Receive ID: {config.receive_id}")
    print(f"Receive ID Type: {config.receive_id_type}")
print(f"Valid: {config.validate()}")
EOF
```

### 测试4: 飞书消息测试

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "../script/hooks")
from common.config import config
from common.feishu_bot import FeishuAppBot

if not config.validate():
    print("❌ Configuration not valid")
    sys.exit(1)

bot = FeishuAppBot(
    config.app_id,
    config.app_secret,
    config.receive_id,
    config.receive_id_type
)

success = bot.send_card_message(
    title="✅ 测试成功 | Test Success",
    content="Claude DX应用机器人集成测试",
    color="green",
    fields=[
        {"name": "状态", "value": "配置正确,消息发送成功"},
        {"name": "接收者类型", "value": config.receive_id_type}
    ]
)

if success:
    print("✅ Message sent successfully!")
    print(f"✅ Check your Feishu {config.receive_id_type}")
else:
    print("❌ Failed to send message")
EOF
```

## 目录结构

```
claude-dx/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── hooks/
│   ├── hooks.json                       # Hook 配置
│   └── requirements.txt                 # Python 依赖
├── script/
│   └── hooks/
│       ├── common/                      # 共享模块
│       │   ├── config.py                # 配置加载器
│       │   ├── logger.py                # 日志工具
│       │   ├── system_notifier.py      # 系统通知模块
│       │   └── feishu_bot.py           # 飞书 API 封装
│       ├── session_start.py            # SessionStart Hook
│       ├── pre_tool_use.py             # PreToolUse Hook
│       ├── post_tool_use.py            # PostToolUse Hook
│       ├── permission_request.py       # PermissionRequest Hook
│       ├── notification.py             # Notification Hook
│       ├── stop.py                     # Stop Hook
│       └── subagent_stop.py            # SubagentStop Hook
├── commands/
│   ├── setup.md                         # /setup 命令
│   └── push.md                          # /push 命令
├── .gitignore
└── README.md                            # 本文档
```

## 故障排查

### 问题: 没有收到通知

**检查清单:**

1. 验证通知类型配置:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, '../script/hooks')
   from common.config import config
   print(f'Notification Type: {config.notification_type}')
   print(f'Valid: {config.validate()}')
   "
   ```

2. 如果使用系统通知:
   ```bash
   # 测试系统通知
   osascript -e 'display notification "测试消息" with title "测试标题"'
   ```

3. 如果使用飞书通知，检查应用权限是否已审核通过:
   - 访问飞书开放平台 → 应用详情 → 权限管理
   - 确认 `im:message` 和 `im:message:send_as_bot` 权限已通过

4. 测试 Token 获取（飞书）:
   ```bash
   python3 << 'EOF'
   import sys
   sys.path.insert(0, "../script/hooks")
   from common.feishu_bot import FeishuTokenManager
   from common.config import config
   from pathlib import Path

   tm = FeishuTokenManager(config.app_id, config.app_secret, Path.home() / ".feishu_token_cache")
   try:
       token = tm.get_token()
       print(f"✅ Token: {token[:20]}...")
   except Exception as e:
       print(f"❌ Error: {e}")
   EOF
   ```

5. 检查 Python 依赖:
   ```bash
   pip3 list | grep requests
   ```

6. 查看 Hook 日志（stderr 输出）

### 问题: Hook 执行超时

**原因:** 网络慢或飞书 API 响应慢

**解决方案:** 增加超时时间，修改 `hooks/hooks.json` 中的 `timeout` 值：

```json
{
  "description": "Claude DX hooks for Feishu notifications",
  "hooks": {
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/script/hooks/notification.py",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/script/hooks/stop.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### 问题: Python 版本不兼容

**要求:** Python 3.7+

**检查版本:**
```bash
python3 --version
```

## 配置选项

### 环境变量(可选)

可以通过环境变量覆盖默认配置：

```bash
export NOTIFICATION_TYPE="system"  # 或 "feishu"
export FEISHU_WEBHOOK_URL="https://..."
export LOG_LEVEL="DEBUG"
export TIMEOUT="15"
```

### 配置文件优先级

配置的加载顺序(优先级从高到低)：

1. 环境变量 (`NOTIFICATION_TYPE`, `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_RECEIVE_ID`, `FEISHU_RECEIVE_ID_TYPE`)
2. `~/.claude/settings.local.json` 中的配置项
3. `~/.claude/settings.json` 中的配置项
4. 默认值 (`notificationType` 默认为 `system`)

## 安全说明

- ✅ 敏感信息自动过滤 (API keys, tokens, passwords)
- ✅ 文件内容仅显示路径，不发送完整内容
- ✅ 参数和输出自动截断
- ✅ Token 缓存文件权限自动设置为 0600 (仅所有者可读写)
- ⚠️ App Secret 包含认证信息，请妥善保管
- ⚠️ 不要将 `settings.local.json` 和 `.feishu_token_cache` 提交到 Git 仓库
- ⚠️ Token 自动缓存到 `~/.feishu_token_cache`，有效期 2 小时

## 路线图

- [x] **MVP1** - Hooks 消息通知（系统通知 + 飞书）
- [ ] **MVP2** - Skills 技能加载
- [ ] **MVP3** - Commands 自定义命令
- [ ] **MVP4** - Agents 自定义代理

## 贡献

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License
