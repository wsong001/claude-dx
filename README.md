# Claude DX

Claude Code 插件,用于飞书/钉钉消息通知和技能加载。

## 功能特性

### MVP1 - Hooks 飞书通知

通过Hooks在Claude Code运行时发送实时消息通知到飞书:

- 🎯 **SessionStart** - 会话开始时通知
- ⚙️ **PreToolUse** - 工具执行前通知
- ✓ **PostToolUse** - 工具执行后通知
- 🔒 **PermissionRequest** - 权限请求时通知
- 🤖 **SubagentStop** - 子代理停止时通知

### 特性

- ✅ 详细模式 - 包含完整上下文信息
- ✅ 敏感信息过滤 - 自动过滤API keys、tokens、passwords等
- ✅ 彩色卡片消息 - 不同Hook类型使用不同颜色
- ✅ 错误隔离 - 通知失败不影响Claude执行
- ✅ 重试机制 - 自动处理API限流

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/claude-dx.git
cd claude-dx
```

### 2. 安装Python依赖

```bash
cd hooks
pip3 install -r requirements.txt
```

### 3. 创建飞书应用并获取配置

#### 3.1 创建飞书应用

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用名称和描述(如: "Claude DX通知机器人")
4. 创建完成后,进入应用详情页面

#### 3.2 获取 App ID 和 App Secret

在"凭证与基础信息"页面:
- **App ID**: 直接可见,格式为 `cli_xxxxxxxxxxxxxx`
- **App Secret**: 点击"查看"按钮获取

#### 3.3 配置应用权限

在"权限管理"页面,申请以下权限(需管理员审核):
- ✅ `im:message` - 获取与发送单聊、群组消息
- ✅ `im:message:send_as_bot` - 以应用的身份发消息

配置后等待管理员审核通过。

#### 3.4 获取接收者ID

**方式1: 发送给用户(个人通知)**

获取用户的 `open_id`:
- 方法A: 飞书管理后台 → 通讯录 → 找到用户 → 查看详情 → 复制 open_id
- 方法B: 让用户给机器人发消息,在事件回调中获取 sender_id

**方式2: 发送到群聊(团队协作)**

获取群聊的 `chat_id`:
1. 创建群聊或使用现有群聊
2. 群设置 → 群机器人 → 添加机器人 → 搜索你的应用名称并添加
3. 通过API获取群组列表,或在群消息事件中获取 chat_id

### 4. 配置应用机器人

#### 方式A: 使用 `/Setup` 命令（推荐）

安装插件后，使用交互式配置向导：

```bash
# 1. 启动 Claude Code（指定插件目录）
claude --plugin-dir /path/to/claude-dx

# 2. 在 Claude Code 中运行
/Setup
```

配置向导会引导你完成：
1. 选择通知方式（应用机器人 or Webhook）
2. 输入飞书 App ID
3. 输入飞书 App Secret
4. 选择通知目标（个人 or 群聊）
5. 输入对应的 ID
6. 自动验证并保存配置

#### 方式B: 手动配置

在 `~/.claude/settings.local.json` 中添加配置:

```json
{
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

**配置说明:**
- `feishuAppId`: 飞书应用ID
- `feishuAppSecret`: 飞书应用密钥
- `feishuReceiveId`: 接收者ID (用户的open_id或群聊的chat_id)
- `feishuReceiveIdType`: 接收者类型
  - `open_id` - 发送给用户(推荐用于个人通知)
  - `chat_id` - 发送到群聊(推荐用于团队协作)

如果 `settings.local.json` 不存在,创建它:

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

### 5. 加载插件

启动Claude Code时加载插件:

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

加载插件后,Claude Code会自动在以下情况发送飞书通知:

1. **会话开始** - 显示会话ID、工作目录、Git状态
2. **工具执行前** - 显示工具名称和输入参数摘要
3. **工具执行后** - 显示执行状态和输出摘要
4. **权限请求** - 提示需要用户审批
5. **子代理停止** - 显示代理执行摘要和统计信息

## 命令

Commands使用纯Markdown文件实现，由Claude Code解释执行。

### `/Setup` - 配置向导

交互式配置飞书应用机器人通知。

**用法**: 在Claude Code中运行 `/Setup`

**实现**: `commands/setup.md`（纯Markdown，无需Python脚本）

**配置内容**:
- Feishu App ID: 从飞书开发者后台获取
- Feishu App Secret: 应用密钥
- 接收者ID: 用户open_id或群聊chat_id
- 接收者类型: open_id（个人）或 chat_id（群聊）

**配置位置**: `~/.claude/settings.local.json`

**验证**: 自动测试API连接，确保配置正确。

## 本地测试

### 测试1: Python依赖验证

```bash
cd hooks
python3 -c "import requests; print('✓ requests installed')"
```

### 测试2: 配置验证

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config

print(f"App ID: {config.app_id[:10]}..." if config.app_id else "App ID: Not configured")
print(f"App Secret: {config.app_secret[:10]}..." if config.app_secret else "App Secret: Not configured")
print(f"Receive ID: {config.receive_id}")
print(f"Receive ID Type: {config.receive_id_type}")
print(f"Valid: {config.validate()}")
EOF
```

预期输出:
```
App ID: cli_xxxxxx...
App Secret: xxxxxxxxxx...
Receive ID: ou_xxxxxxxxxx
Receive ID Type: open_id
Valid: True
```

### 测试3: Token获取测试

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
from common.config import config
from common.feishu_bot import FeishuTokenManager
from pathlib import Path

if not config.validate():
    print("❌ Configuration not valid")
    sys.exit(1)

token_manager = FeishuTokenManager(
    config.app_id,
    config.app_secret,
    Path.home() / ".feishu_token_cache"
)

try:
    token = token_manager.get_token()
    print(f"✅ Token obtained: {token[:20]}...")
    print(f"✅ Token cached to: {Path.home() / '.feishu_token_cache'}")
except Exception as e:
    print(f"❌ Failed to get token: {e}")
EOF
```

### 测试4: 飞书消息测试

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, "hooks")
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

### 测试5: 单个Hook测试

```bash
cd /Users/admin/Documents/GitHub/claude-dx

echo '{"session_id":"test-123","timestamp":"2024-02-04T12:00:00Z","cwd":"/tmp","git_repo":true,"git_branch":"main"}' | \
  python3 hooks/entry_points/session_start_hook.py 2>&1
```

应该:
- 发送SessionStart消息到飞书
- stdout输出原始JSON
- stderr包含日志信息
- 检查飞书是否收到蓝色卡片消息

## 目录结构

```
claude-dx/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── hooks/
│   ├── hooks.json                       # Hook配置
│   ├── common/
│   │   ├── config.py                    # 配置加载器
│   │   ├── logger.py                    # 日志工具
│   │   └── feishu_bot.py               # 飞书API封装
│   ├── handlers/
│   │   ├── base_handler.py             # 基础处理器
│   │   ├── session_start.py            # SessionStart处理器
│   │   ├── pre_tool_use.py             # PreToolUse处理器
│   │   ├── post_tool_use.py            # PostToolUse处理器
│   │   ├── permission_request.py       # PermissionRequest处理器
│   │   └── subagent_stop.py            # SubagentStop处理器
│   ├── entry_points/
│   │   ├── session_start_hook.py       # SessionStart入口
│   │   ├── pre_tool_use_hook.py        # PreToolUse入口
│   │   ├── post_tool_use_hook.py       # PostToolUse入口
│   │   ├── permission_request_hook.py  # PermissionRequest入口
│   │   └── subagent_stop_hook.py       # SubagentStop入口
│   └── requirements.txt                # Python依赖
├── .gitignore
├── .env.example                        # 环境变量模板
└── README.md                           # 本文档
```

## 故障排查

### 问题: 没有收到飞书通知

**检查清单:**

1. 验证应用机器人配置正确:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, 'hooks')
   from common.config import config
   print(f'App ID: {config.app_id}')
   print(f'Receive ID: {config.receive_id}')
   print(f'Valid: {config.validate()}')
   "
   ```

2. 检查应用权限是否已审核通过:
   - 访问飞书开放平台 → 应用详情 → 权限管理
   - 确认 `im:message` 和 `im:message:send_as_bot` 权限已通过

3. 测试Token获取:
   ```bash
   python3 << 'EOF'
   import sys
   sys.path.insert(0, "hooks")
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

4. 检查Python依赖:
   ```bash
   pip3 list | grep requests
   ```

5. 查看Token缓存:
   ```bash
   cat ~/.feishu_token_cache | python3 -m json.tool
   ```

6. 查看Hook日志(stderr输出)

### 问题: Hook执行超时

**原因:** 网络慢或飞书API响应慢

**解决方案:** 增加超时时间,修改 `hooks/hooks.json`:

```json
{
  "timeout": 30
}
```

### 问题: Python版本不兼容

**要求:** Python 3.7+

**检查版本:**
```bash
python3 --version
```

## 配置选项

### 环境变量(可选)

可以通过环境变量覆盖默认配置:

```bash
export FEISHU_WEBHOOK_URL="https://..."
export LOG_LEVEL="DEBUG"
export TIMEOUT="15"
```

### 配置文件优先级

应用机器人配置的加载顺序(优先级从高到低):

1. 环境变量 (`FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_RECEIVE_ID`, `FEISHU_RECEIVE_ID_TYPE`)
2. `~/.claude/settings.local.json` 中的配置项
3. `~/.claude/settings.json` 中的配置项
4. 默认值 (`feishuReceiveIdType` 默认为 `open_id`)

## 安全说明

- ✅ 敏感信息自动过滤 (API keys, tokens, passwords)
- ✅ 文件内容仅显示路径,不发送完整内容
- ✅ 参数和输出自动截断
- ✅ Token缓存文件权限自动设置为 0600 (仅所有者可读写)
- ⚠️ App Secret 包含认证信息,请妥善保管
- ⚠️ 不要将 `settings.local.json` 和 `.feishu_token_cache` 提交到Git仓库
- ⚠️ Token自动缓存到 `~/.feishu_token_cache`,有效期2小时

## 路线图

- [x] **MVP1** - Hooks飞书通知
- [ ] **MVP2** - Skills 技能加载
- [ ] **MVP3** - Commands 自定义命令
- [ ] **MVP4** - Agents 自定义代理

## 贡献

欢迎提交Issue和Pull Request!

## 许可证

MIT License
