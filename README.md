# Claude DX

Claude Code 插件，用于飞书/系统消息通知。

## 功能特性

### MVP1 - Hooks 消息通知

通过 Hooks 在 Claude Code 运行时发送实时消息通知：

- 🔒 **PermissionRequest** - 权限请求时通知
- 🤖 **Stop** - 会话停止时通知

### 通知方式

#### 系统通知（推荐用于本地开发）
- ✅ 无需配置，开箱即用

#### 飞书应用机器人（推荐用于远程通知）
- ✅ 支持远程通知
- ✅ 支持富文本卡片消息
- ✅ 适合团队协作
- ⚠️ 需要配置飞书应用

## 安装

使用 Claude CLI 一键安装：

```bash
/plugin marketplace add wsong001/claude-dx

/plugin install claude-dx@claude-dx
```

重启 Claude Code 即可生效。

## 配置

运行配置向导：

```bash
/claude-dx:setup
```

配置完成后立即生效，无需重启。


## 命令

Commands 使用纯 Markdown 文件实现，由 Claude Code 解释执行。

### `/setup` - 配置向导

**配置位置**: `~/.claude/settings.local.json`

**验证**: 自动测试 API 连接，确保配置正确。

## 本地测试

### 测试系统通知

```bash
osascript -e 'display notification "测试消息" with title "Claude DX"'
```

## 目录结构

```
claude-dx/
├── .claude-plugin/
│   ├── plugin.json                      # 插件清单
│   └── hooks.json                       # Hook 配置
├── hooks/
│   └── hooks.json                       # Hook 配置
├── script/
│   └── hooks/
│       ├── common/                      # 共享模块
│       │   ├── config.py                # 配置加载器
│       │   ├── logger.py                # 日志工具
│       │   ├── system_notifier.py      # 系统通知模块
│       │   └── feishu_bot.py           # 飞书 API 封装
│       ├── handlers/                    # Hook 处理器
│       │   ├── base.py                 # 抽象基类
│       │   ├── session.py              # SessionStart/Stop
│       │   ├── tool.py                 # PreToolUse/PostToolUse
│       │   ├── permission.py           # PermissionRequest
│       │   ├── notification.py         # Notification
│       │   └── subagent.py             # SubagentStop
│       ├── utils/                       # 工具函数
│       │   ├── filters.py              # 敏感信息过滤
│       │   └── formatters.py           # 数据格式化
│       └── hook_runner.py              # 统一入口点
├── commands/
│   ├── setup.md                         # /setup 命令
│   └── push.md                          # /push 命令
├── .gitignore
└── README.md                            # 本文档
```

## 故障排查

### 问题: 没有收到通知

**检查清单:**

1. **系统通知**
   - 测试系统通知：`osascript -e 'display notification "测试" with title "测试"'`
   - 检查系统通知权限：系统设置 → 通知 → 终端/Claude Code

2. **飞书通知**
   - 重新运行 `/claude-dx:setup` 验证配置
   - 检查飞书应用权限是否已审核通过（`im:message` 和 `im:message:send_as_bot`）
   - 访问飞书开放平台 → 应用详情 → 权限管理

3. **Python 环境**
   - 检查 Python 版本：`python3 --version`（需要 3.7+）
   - Python 依赖会在插件安装时自动安装

4. **查看日志**
   - Hook 执行日志输出到 stderr，可在 Claude Code 中查看

### 问题: Hook 执行超时

**原因:** 网络慢或飞书 API 响应慢

**解决方案:** Hook 配置已设置 10 秒超时。如仍超时，可能是网络问题。考虑：
- 检查网络连接
- 切换到系统通知（`/claude-dx:setup`）

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

## 贡献

欢迎提交 Issue 和 Pull Request!

## 许可证

MIT License
