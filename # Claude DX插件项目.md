# Claude DX插件项目

该项目是一个 Claude Code Plugin 项目，项目名称为 Claude DX。该项目提供给 marketplace 插件市场，能够被 Claude 用户自主安装。项目主要功能是：

1. **消息通知** - Claude Code 运行时，触发 hooks，发送消息通知（支持系统通知和飞书）
2. **技能加载** - Claude Code 运行时，触发 hooks，通过条件匹配到 skill，使 Claude 可以预先加载这些 skill，使 Claude 变身成为专家

## 创建目录结构

```
claude-dx/               # 项目名称
├── .claude-plugin/
│   └── plugin.json      # 插件清单（必需）
├── commands/            # 自定义命令
│   └── setup.md         # 配置向导
├── skills/              # 技能
├── agents/              # 代理
└── hooks/               # 钩子
```

## hooks（MVP1 - Completed）

hook 触发节点是 SessionStart、Stop、PreToolUse、PostToolUse、PermissionRequest、Notification 和 SubagentStop，需要在触发节点执行一个 Python 文件，Python 文件逻辑是触发通知接口，将消息发送给用户。

### 支持的通知方式

#### 系统通知（默认）
- macOS 右上角原生通知
- 无需配置，开箱即用
- 适合本地开发场景

#### 飞书应用机器人
- 飞书富文本卡片消息
- 需要配置 App ID 和 App Secret
- 适合远程通知和团队协作

### Hook 类型

| Hook 类型 | 触发时机 | 通知内容 |
|-----------|----------|----------|
| SessionStart | 会话开始 | 会话 ID、工作目录、Git 状态 |
| Stop | 会话结束 | 停止状态、统计信息 |
| PreToolUse | 工具执行前 | 工具名称、参数摘要 |
| PostToolUse | 工具执行后 | 执行状态、输出摘要 |
| PermissionRequest | 权限请求 | 权限类型、请求详情 |
| Notification | 系统通知 | 各类系统提示 |
| SubagentStop | 子代理停止 | 代理执行摘要 |

### 组件统计

- **Hooks**: 7 个 (SessionStart, Stop, PreToolUse, PostToolUse, PermissionRequest, Notification, SubagentStop)
- **Commands**: 1 个 (Setup)
- **Skills**: 0 个
- **Agents**: 0 个

## skills（MVP2）

## commands（MVP3 - Completed）

commands 是斜杠指令，用户可以通过这些命令快速配置和管理插件。

**实现方式**: 纯 Markdown 文件 - 命令定义和执行逻辑都在 `.md` 文件中，由 Claude Code 解释执行。

### 已实现的 Commands

#### `/Setup` - 配置向导

交互式配置通知功能：

**配置选项**:
1. 选择通知方式
   - **系统通知** - macOS 右上角通知（无需配置，本地使用）
   - **飞书应用机器人** - 需要配置飞书应用（推荐用于远程通知）

2. 如果选择飞书，收集以下信息：
   - 飞书 App ID
   - 飞书 App Secret
   - 通知目标（个人账号/飞书群）
   - 接收者 ID

**使用方法**:
```bash
claude --plugin-dir /Users/admin/Documents/GitHub/claude-dx
# 在 Claude Code 中运行
/Setup
```

**实现文件**: `commands/setup.md`（纯 Markdown）

**配置文件**: `~/.claude/settings.local.json`

系统通知配置：
```json
{
  "notificationType": "system"
}
```

飞书通知配置：
```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

**技术特点**:
- ✅ 使用 AskUserQuestion 工具收集用户输入
- ✅ 通过 Write 工具保存配置（深度合并）
- ✅ 使用 Bash 工具设置文件权限（0o600）
- ✅ 输入验证（正则表达式）
- ✅ 可选的 API 连接测试

### 通知方式对比

| 特性 | 系统通知 | 飞书应用机器人 |
|------|---------|---------------|
| 配置复杂度 | 无需配置 | 需要 App ID/Secret |
| 通知范围 | 本地通知 | 远程通知 |
| 消息丰富度 | 简单文本 | 富文本卡片 |
| 依赖性 | 仅需 macOS | 需要网络和飞书 API |
| 适用场景 | 本地开发、个人使用 | 远程监控、团队协作 |

## agents（MVP4）

### 本地测试

```bash
claude --plugin-dir ./claude-dx
```
