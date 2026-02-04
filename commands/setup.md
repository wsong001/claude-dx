---
description: Configure Claude DX plugin for Feishu notifications
---

# Setup - Claude DX Configuration Wizard

Interactive setup wizard for configuring Feishu app robot notifications.

## Instructions

When user runs `/Setup`, follow these steps:

### Step 1: Welcome Message

Display a friendly welcome message:

```
╔════════════════════════════════════════════════════════════╗
║  Claude DX 配置向导 / Setup Wizard                         ║
║  Version 0.2.0                                             ║
╚════════════════════════════════════════════════════════════╝

欢迎使用 Claude DX 配置向导！
本向导将帮助你配置飞书通知功能。
```

### Step 2: Collect Configuration

Use the AskUserQuestion tool to collect the following information:

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

### Step 3: Build Configuration Object

Construct the configuration object:

```json
{
  "feishuAppId": "<collected_app_id>",
  "feishuAppSecret": "<collected_app_secret>",
  "feishuReceiveId": "<collected_receiver_id>",
  "feishuReceiveIdType": "<open_id or chat_id based on selection>"
}
```

### Step 4: Validate Configuration (Optional)

Optionally test the API connection by:
1. Making a POST request to `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
2. Payload: `{"app_id": "<app_id>", "app_secret": "<app_secret>"}`
3. Check if response code is 0 (success)

If validation fails, warn the user but continue with saving.

### Step 5: Save Configuration

1. **Read existing config** (if exists): `~/.claude/settings.local.json`
2. **Deep merge**: Merge new config into existing config (preserve other keys)
3. **Write config**: Save to `~/.claude/settings.local.json`
4. **Set permissions**: Run `chmod 600 ~/.claude/settings.local.json`

**Deep Merge Logic**:
- Preserve all existing keys in the config file
- Only update/add the Feishu-related keys
- Example: If config has `{"otherKey": "value"}`, result should be `{"otherKey": "value", "feishuAppId": "...", ...}`

### Step 6: Display Completion Message

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
  2. 开始对话，将自动收到飞书通知

配置文件位置: ~/.claude/settings.local.json

祝你使用愉快！🚀
```

## Configuration Format

The saved configuration should follow this format:

```json
{
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

## Validation Rules

- **feishuAppId**: Must match regex `^cli_[a-zA-Z0-9]{16}$`
- **feishuAppSecret**: Minimum 32 characters
- **feishuReceiveId**:
  - If type is "open_id": Must match regex `^ou_[a-zA-Z0-9]+$`
  - If type is "chat_id": Must match regex `^oc_[a-zA-Z0-9]+$`
- **feishuReceiveIdType**: Must be either "open_id" or "chat_id"

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
