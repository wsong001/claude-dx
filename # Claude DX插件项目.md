# Claude DX插件项目
该项目是一个Claude Code Plugin项目，项目名称为Claude DX。该项目提供给marketplace插件市场，能够被Claude用户自主安装。项目主要功能是：
1. Claude Code运行时，触发hooks，给对应用户发送消息提示。
2. Claude Code运行时，触发hooks，通关条件匹配到skill，使claude可以预先加载这些skill，使claude变身成为专家。

## 创建目录结构
claude-dx/               # 项目名称
├── .claude-plugin/
│   └── plugin.json      # 插件清单（必需）
├── commands/            # 自定义命令
|    └──install.md       # 插件安装文件
├── skills/              # 技能
├── agents/              # 代理
└── hooks/               # 钩子

## commands
commands是斜杠指令，用户可以通过install.md快速安装该插件

## hooks（MVP1）
hook触发节点是SessionStart、PreToolUse、PostToolUse、PermissionRequest和SubagentStop，需要在触发节点执行一个Python文件，Python文件逻辑是触发飞书机器人发送消息通知接口，将消息发送给用户的飞书账号。

## skills（MVP2）

## commands（MVP3 - Completed）

commands是斜杠指令，用户可以通过这些命令快速配置和管理插件。

**实现方式**: 纯Markdown文件 - 命令定义和执行逻辑都在 `.md` 文件中，由Claude Code解释执行。

### 已实现的Commands

#### `/Setup` - 配置向导

交互式配置飞书应用机器人通知：
- 选择通知方式（应用机器人/Webhook）
- 收集飞书App ID和App Secret
- 选择通知目标（个人账号/飞书群）
- 验证配置有效性
- 自动保存到 `~/.claude/settings.local.json`

**使用方法**:
```bash
claude --plugin-dir /Users/admin/Documents/GitHub/claude-dx
# 在Claude Code中运行
/Setup
```

**实现文件**: `commands/setup.md`（纯Markdown，约150行）

**配置文件**: `~/.claude/settings.local.json`
```json
{
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

**技术特点**:
- ✅ 使用AskUserQuestion工具收集用户输入
- ✅ 通过Write工具保存配置（深度合并）
- ✅ 使用Bash工具设置文件权限（0o600）
- ✅ 输入验证（正则表达式）
- ✅ 可选的API连接测试

## 当前组件统计

- Hooks: 5个 (SessionStart, PreToolUse, PostToolUse, PermissionRequest, SubagentStop)
- Commands: 1个 (Setup)
- Skills: 0个
- Agents: 0个

## agents（MVP4）

### 本地测试：
claude --plugin-dir ./claude-dx