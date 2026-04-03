---
name: setup
description: Configure Claude DX plugin for notifications
---

# Setup - Claude DX Configuration Wizard

Interactive setup wizard for configuring Claude DX notifications.

## Instructions

When user runs `/setup`, follow these steps **in order**. Each step includes branching logic — follow the path that matches the user's situation.

### Step 1: Welcome

Display:

```
===========================================================
  Claude DX 配置向导 / Setup Wizard
  Version 0.3.0
===========================================================

配置通知方式，让 Claude 在任务完成时及时通知你。
```

### Step 2: Detect Existing Configuration

**Action**: Read `~/.claude/settings.local.json` using the Read tool. Check for the presence of notification keys: `notificationType`, `feishuAppId`, `feishuAppSecret`, `feishuReceiveId`, `feishuReceiveIdType`.

**If config exists**, display a summary (mask App Secret — show first 4 + `****` + last 4 characters):

```
检测到已有配置：

  通知类型    : feishu
  App ID     : cli_xxxxxxxxxxxx
  App Secret : XXXX****XXXX
  接收者类型  : open_id
  接收者 ID  : ou_xxxxxxxxxxxx
```

Then ask the user to choose:

```
请选择操作：

1. 重新配置全部
2. 修改特定字段
3. 测试现有配置
```

- User selects **1** → Go to **Step 3**
- User selects **2** → Go to **Step 2b**
- User selects **3** → Go to **Step 6**

**If no config exists**, display:

```
未检测到通知配置，将引导你完成首次配置。
```

Then proceed to **Step 3**.

### Step 2b: Modify Specific Fields

Present all editable fields with current values:

```
请选择要修改的字段（输入编号，多个用逗号分隔）：

1. 通知类型 (当前: feishu)
2. App ID (当前: cli_xxxx...)
3. App Secret (当前: ****...****)
4. 接收者类型 (当前: open_id)
5. 接收者 ID (当前: ou_xxxx...)
```

For each selected field, jump to the corresponding collection sub-step:
- 1 → Step 3 (notification type selection only, then skip to Step 5)
- 2 → Step 4a
- 3 → Step 4b
- 4 → Step 4c
- 5 → Step 4d

Unselected fields retain their current values from the existing config. After collecting all selected fields, jump to **Step 5**.

### Step 3: Notification Type Selection

```
通知类型

你希望通过什么方式接收通知？

1. 飞书 (Feishu) — 通过飞书应用机器人发送卡片消息
2. 系统通知 (System) — 使用 macOS 原生通知
```

**If user selects "系统通知"**:
- Set `notificationType` to `"system"`
- Display warning:

```
注意：系统通知功能正在开发中。配置将被保存，但通知暂时不会生效。
```

- Skip Steps 3a and 4, jump to **Step 5**

**If user selects "飞书"**:
- Set `notificationType` to `"feishu"`
- Proceed to **Step 3a**

### Step 3a: Python Environment Check (Feishu Only)

```
检查 Python 环境...
```

1. Run `python3 --version`
2. Run `python3 -c "import requests; print(requests.__version__)"`

**Both OK**:
```
Python 环境检查完成
  Python   : <version> ... OK
  requests : <version> ... OK
```

Proceed to **Step 4**.

**Python missing**:
```
Python 3 未安装。飞书通知需要 Python 3。
安装方式：brew install python3 (macOS)
```

Ask user whether to continue or cancel.

**requests missing**:
```
requests 库未安装。是否自动安装？(y/n)
```

If yes, run `pip3 install requests` and verify. If no, warn that notifications won't work but continue.

### Step 4: Collect Feishu Credentials

Each sub-step shows a progress indicator. After each input, briefly confirm what was collected.

#### Step 4a: App ID

```
[Step 1/4] 飞书应用 App ID

请输入飞书应用的 App ID：

  格式    : cli_ 开头 + 16 位字母数字
  示例    : cli_a1b2c3d4e5f6g7h8
  获取方式 : 飞书开发者后台 → 凭证与基础信息 → App ID
```

**Validation**: Must match `^cli_[a-zA-Z0-9]{16}$`

On failure:
```
格式错误。App ID 应为 cli_ 开头加 16 位字母数字。请重新输入：
```

#### Step 4b: App Secret

```
[Step 2/4] 飞书应用 App Secret

请输入飞书应用的 App Secret：

  格式    : 32 位以上字母数字组合
  获取方式 : 飞书开发者后台 → 凭证与基础信息 → App Secret（点击查看）
```

**Validation**: Minimum 32 characters.

#### Step 4c: Receive ID Type

```
[Step 3/4] 通知接收者类型

通知发送给谁？

1. 我自己 — 需要 open_id
2. 群聊   — 需要 chat_id
```

#### Step 4d: Receive ID

Based on Step 4c selection:

**open_id**:
```
[Step 4/4] 接收者 Open ID

请输入你的 Open ID：

  格式    : ou_ 开头 + 字母数字
  示例    : ou_a1b2c3d4e5f6g7h8
  获取方式 : 通过飞书开放平台 API 获取用户信息
```

**Validation**: Must match `^ou_[a-zA-Z0-9]+$`

**chat_id**:
```
[Step 4/4] 群聊 Chat ID

请输入群聊 Chat ID：

  格式    : oc_ 开头 + 字母数字
  示例    : oc_a1b2c3d4e5f6g7h8
  获取方式 : 飞书群聊设置 → 群 ID
```

**Validation**: Must match `^oc_[a-zA-Z0-9]+$`

### Step 5: Configuration Summary and Confirmation

Display all values to be saved (App Secret masked):

```
===========================================================
  配置摘要
===========================================================

  通知类型    : feishu
  App ID     : cli_a1b2c3d4e5f6g7h8
  App Secret : XXXX************************XXXX
  接收者类型  : open_id
  接收者 ID  : ou_xxxxxxxxxxxx

  配置文件: ~/.claude/settings.local.json
===========================================================

确认保存？

1. 保存并继续
2. 重新配置
3. 取消
```

- **保存并继续**:
  1. Read existing `~/.claude/settings.local.json` (if exists)
  2. Deep-merge: preserve all existing keys, only update/add notification keys
  3. Write merged config back to `~/.claude/settings.local.json`
  4. Run `chmod 600 ~/.claude/settings.local.json`
  5. Proceed to **Step 6**

- **重新配置** → Go back to **Step 3**
- **取消** → Display `配置已取消。` and exit

### Step 6: Test Notification (Optional)

```
配置已保存！

是否发送测试通知来验证配置？

1. 发送测试通知
2. 跳过
```

**If user selects "发送测试通知" and notificationType is "feishu"**:

Run via Bash:
```bash
echo '{"stop_reason":"completed","session_id":"test-setup"}' | python3 <plugin_root>/script/hooks/stop.py
```

Where `<plugin_root>` is the plugin directory path (the directory containing this setup.md file's parent).

**On success** (stderr contains "notification sent"):
```
测试通知发送成功！请检查你的飞书消息。
如果收到了标题为"会话结束"的卡片消息，说明配置正确。
```

Proceed to **Step 7**.

**On failure**:
```
测试通知发送失败。

可能原因：
  - App ID 或 App Secret 不正确
  - 应用未授权消息发送权限
  - 接收者 ID 无效或机器人无访问权限
  - 网络连接问题

请选择：
1. 重新配置凭证
2. 忽略并继续
```

- **重新配置凭证** → Go to **Step 4a**
- **忽略并继续** → Proceed to **Step 7**

**If notificationType is "system"**: Skip test, display `系统通知功能开发中，跳过测试。`, proceed to **Step 7**.

**If user selects "跳过"**: Proceed to **Step 7**.

### Step 7: Completion

```
===========================================================
  配置完成！
===========================================================

  配置文件 : ~/.claude/settings.local.json
  通知类型 : <notificationType>

  下一步：
    - Claude Code 将自动使用新配置
    - 会话结束时将自动发送通知
    - 随时运行 /setup 重新配置
===========================================================
```

## Configuration Format

```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

## Validation Rules

- **notificationType**: Must be `"feishu"` or `"system"`
- **feishuAppId**: Must match regex `^cli_[a-zA-Z0-9]{16}$`
- **feishuAppSecret**: Minimum 32 characters
- **feishuReceiveId**:
  - If type is `"open_id"`: Must match regex `^ou_[a-zA-Z0-9]+$`
  - If type is `"chat_id"`: Must match regex `^oc_[a-zA-Z0-9]+$`
- **feishuReceiveIdType**: Must be either `"open_id"` or `"chat_id"`

## Error Handling

- If user cancels at any step: display `配置已取消。`
- If validation fails: show error and allow retry
- If file write fails: show error with troubleshooting steps
- Always preserve existing configuration keys when merging

## Security Notes

- File permissions must be set to 600 (owner read/write only)
- Never display the full App Secret — always mask middle characters
- Validate all inputs before saving
