---
description: Configure Claude DX plugin for notifications
---

# Setup - Claude DX Configuration Wizard

Interactive setup wizard for configuring Claude DX notifications.

## Instructions

When user runs `/Setup`, follow these steps:

### Step 1: Welcome Message

Display a friendly welcome message:

```
╔════════════════════════════════════════════════════════════╗
║  Claude DX 配置向导 / Setup Wizard                         ║
║  Version 0.3.0                                             ║
╚════════════════════════════════════════════════════════════╝

欢迎使用 Claude DX 配置向导！
本向导将帮助你配置消息通知功能。
```

### Step 2: 选择通知方式

Use the AskUserQuestion tool to ask the user which notification method they prefer:

**Header**: "通知方式"
**Question**: "请选择消息通知方式："
**Options**:
1. "飞书应用机器人" - 需要配置飞书应用（推荐用于远程通知）
2. "系统通知" - macOS 右上角通知（无需配置，本地使用）

**Logic Based on User Choice**:

| 用户选择 | 后续操作 |
|----------|----------|
| 飞书应用机器人 | 执行 Step 3-7（收集 App ID、Secret 等） |
| 系统通知 | 跳到 Step 8（直接保存配置，跳过飞书配置） |

### Step 3: Collect Feishu Configuration (Only if Feishu selected)

If user selected "飞书应用机器人", use the AskUserQuestion tool to collect the following information:

#### Question 1: Feishu App ID
- **Header**: "App ID"
- **Question**: "请输入飞书应用的 App ID（从飞书开发者后台获取）"
- **Validation**: Must start with `cli_` and be 20 characters total (e.g., `cli_1234567890abcdef`)
- **Hint**: "在飞书开发者后台 → 凭证与基础信息 → App ID"

#### Question 2: Feishu App Secret
- **Header**: "App Secret"
- **Question**: "请输入飞书应用的 App Secret（应用密钥）"
- **Validation**: Minimum 32 characters
- **Hint**: "在飞书开发者后台 → 凭证与基础信息 → App Secret（点击查看）"

#### Question 3: Notification Target
- **Header**: "通知目标"
- **Question**: "选择通知发送到哪里？"
- **Options**:
  1. "个人账号" - 需要用户的 open_id
  2. "飞书群" - 需要群聊的 chat_id

#### Question 4: Receiver ID
- **Header**: "接收者ID"
- **Question**: Based on previous answer:
  - If "个人账号": "请输入用户的 open_id（格式：ou_xxxxxxxxxxxxxx）"
  - If "飞书群": "请输入群聊的 chat_id（格式：oc_xxxxxxxxxxxxxx）"
- **Validation**:
  - open_id: Must start with `ou_`
  - chat_id: Must start with `oc_`

### Step 4: Build Configuration Object

Construct the configuration object based on user selection:

**If Feishu selected:**
```json
{
  "notificationType": "feishu",
  "feishuAppId": "<collected_app_id>",
  "feishuAppSecret": "<collected_app_secret>",
  "feishuReceiveId": "<collected_receiver_id>",
  "feishuReceiveIdType": "<open_id or chat_id based on selection>"
}
```

**If System selected:**
```json
{
  "notificationType": "system"
}
```

### Step 5: Validate Configuration (Optional for Feishu)

If user selected Feishu, optionally test the API connection by:
1. Making a POST request to `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
2. Payload: `{"app_id": "<app_id>", "app_secret": "<app_secret>"}`
3. Check if response code is 0 (success)

If validation fails, warn the user but continue with saving.

### Step 6: Save Configuration

1. **Read existing config** (if exists): `~/.claude/settings.local.json`
2. **Deep merge**: Merge new config into existing config (preserve other keys)
3. **Write config**: Save to `~/.claude/settings.local.json`
4. **Set permissions**: Run `chmod 600 ~/.claude/settings.local.json`

**Deep Merge Logic**:
- Preserve all existing keys in the config file
- Only update/add the notification-related keys
- Example: If config has `{"otherKey": "value"}`, result should be `{"otherKey": "value", "notificationType": "...", ...}`

### Step 7: Display Completion Message

Show success message with plugin statistics:

```
╔════════════════════════════════════════════════════════════╗
║  ✅ 配置完成！                                             ║
╚════════════════════════════════════════════════════════════╝

📊 当前组件统计:
  - Agents: 0
  - Commands: 1 (/Setup)
  - Hooks: 5
  - Skills: 0

🎯 下一步:
  1. Claude Code 将自动使用新配置
  2. 开始对话，将自动收到通知

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
