---
description: Configure Claude DX plugin for notifications
---

# Setup - Claude DX Configuration Wizard

Interactive setup wizard for configuring Claude DX notifications.

## Instructions

When user runs `/setup`, follow these steps:

### Step 1: 欢迎消息

```
╔════════════════════════════════════════════════════════════╗
║  Claude DX 配置向导 / Setup Wizard                         ║
║  Version 0.3.0                                             ║
╚════════════════════════════════════════════════════════════╝

🎯 Claude DX 配置向导

配置通知方式，让 Claude 及时通知你。
```

### Step 2: 选择通知方式

Use the AskUserQuestion tool to ask the user which notification method they prefer:

**Header**: "通知方式"
**Question**: "选择通知方式："
**Options**:
1. "飞书应用机器人消息通知" - 适合远程通知和团队协作
2. "系统消息通知" - 适合本地使用，无需配置 [推荐]

**Logic Based on User Choice**:

| 用户选择 | 后续操作 |
|----------|----------|
| 飞书应用机器人消息通知 | 执行 Step 3（收集飞书配置） |
| 系统消息通知 | 跳到 Step 4（直接保存配置） |

### Step 3: 收集飞书配置（仅选择飞书时执行）

If user selected "飞书应用机器人消息通知", follow these sub-steps:

#### Step 3.0: 检查 Python 环境

飞书通知需要 Python 和 requests 库。自动检查并安装：

1. **检查 Python**：运行 `python3 --version`
2. **检查 requests**：运行 `python3 -c "import requests; print(requests.__version__)"`

**如果缺少依赖，自动安装**：
- 如果 Python 未安装：提示用户安装 Python（macOS: `brew install python3`）
- 如果 requests 未安装：运行 `pip3 install requests`

**显示进度消息**：
```
🔍 正在检查 Python 环境...
```

检查完成后，显示结果：
```
✅ Python 环境检查完成
  Python: <version>
  requests: <version>
```

#### Step 3.1: 选择接收者类型

**Header**: "飞书应用机器人App Id和App Secret"
**Question**: "收集飞书应用机器人App Id和App Secret"
**Options**:
1. "App Id" - 请访问飞书开放平台后台查看App Id
2. "App Secret" - 请访问飞书开放平台后台查看App Secret

**Header**: "接收者"
**Question**: "通知发送给谁？"
**Options**:
1. "我自己" - 需要 open_id
2. "群聊" - 需要 chat_id

**提示格式示例**：

```
请输入飞书应用的 App ID：

格式示例：cli_1234567890abcdef
获取方式：飞书开发者后台 → 凭证与基础信息 → App ID
```

Wait for user input, then:

```
请输入飞书应用的 App Secret：

格式示例：32位以上的字母数字组合
获取方式：飞书开发者后台 → 凭证与基础信息 → App Secret（点击查看）
```

Wait for user input, then:

```
请输入接收者 ID：

- 如果是"我自己"：输入 open_id（格式：ou_xxxxxxxxxxxxxx）
- 如果是"群聊"：输入 chat_id（格式：oc_xxxxxxxxxxxxxx）

获取方式：
  - open_id：通过飞书开放平台 API 获取用户信息
  - chat_id：在飞书群聊设置中查看群 ID
```

**Validation**:
- App ID: Must start with `cli_` and be 20+ characters
- App Secret: Minimum 32 characters
- open_id: Must start with `ou_`
- chat_id: Must start with `oc_`

### Step 4: 保存配置

1. **读取现有配置**（如果存在）：`~/.claude/settings.local.json`
2. **深度合并**：将新配置合并到现有配置中（保留其他键）
3. **写入配置**：保存到 `~/.claude/settings.local.json`
4. **设置权限**：运行 `chmod 600 ~/.claude/settings.local.json`

**深度合并逻辑**：
- 保留配置文件中的所有现有键
- 仅更新/添加通知相关的键
- 示例：如果配置有 `{"otherKey": "value"}`，结果应为 `{"otherKey": "value", "notificationType": "...", ...}`

### Step 5: 显示完成消息

```
╔════════════════════════════════════════════════════════════╗
║  ✅ 配置完成！                                             ║
╚════════════════════════════════════════════════════════════╝

🎯 下一步:
  - Claude Code 将自动使用新配置
  - 开始对话，将自动收到通知

配置文件位置: ~/.claude/settings.local.json

祝你使用愉快！🚀
```

## Configuration Format

### Feishu Notification

```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

### System Notification

```json
{
  "notificationType": "system"
}
```

## Validation Rules

### Feishu Configuration
- **notificationType**: Must be "feishu"
- **feishuAppId**: Must match regex `^cli_[a-zA-Z0-9]{16}$`
- **feishuAppSecret**: Minimum 32 characters
- **feishuReceiveId**:
  - If type is "open_id": Must match regex `^ou_[a-zA-Z0-9]+$`
  - If type is "chat_id": Must match regex `^oc_[a-zA-Z0-9]+$`
- **feishuReceiveIdType**: Must be either "open_id" or "chat_id"

### System Configuration
- **notificationType**: Must be "system"

## Error Handling

- If user cancels at any step, display: "⚠️ 配置已取消"
- If validation fails, show error but allow user to retry or skip
- If file write fails, show error message with troubleshooting steps
- Always preserve existing configuration when merging

## Security Notes

- File permissions must be set to 600 (owner read/write only)
- Never log or display the full App Secret
- Validate all inputs before saving
- Use atomic write operations (write to temp file, then move)

## Notification Method Comparison

| 特性 | 飞书应用机器人 | 系统通知 |
|------|---------------|----------|
| 配置复杂度 | 需要配置 App ID/Secret | 无需配置 |
| 通知范围 | 远程通知（飞书） | 本地通知（macOS 右上角） |
| 消息丰富度 | 支持富文本卡片 | 简单文本 |
| 依赖性 | 需要网络和飞书 API | 仅需 macOS |
| 适用场景 | 远程监控、团队协作 | 本地开发、个人使用 |
