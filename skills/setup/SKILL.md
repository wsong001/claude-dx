---
name: setup
description: Claude DX 配置向导 — 配置飞书通知凭证和通知方式
---

# Setup - Claude DX 配置向导

交互式配置向导，用于配置 Claude DX 通知。

## 使用说明

当用户运行 `/setup` 时，按以下步骤**依次执行**。每个步骤包含分支逻辑 — 按用户的实际情况选择对应路径。

### 第一步：欢迎

显示：

```
===========================================================
  Claude DX 配置向导 / Setup Wizard
  Version 1.0.0
===========================================================

配置通知方式，让 Claude 在任务完成时及时通知你。
```

### 第二步：检测现有配置

**操作**：使用 Read 工具读取 `~/.claude/settings.local.json`，检查是否存在通知相关字段：`notificationType`、`feishuAppId`、`feishuAppSecret`、`feishuReceiveId`、`feishuReceiveIdType`。

**如果配置已存在**，显示摘要（App Secret 脱敏 — 显示前4位 + `****` + 后4位）：

```
检测到已有配置：

  通知类型    : feishu
  App ID     : cli_xxxxxxxxxxxx
  App Secret : XXXX****XXXX
  接收者类型  : open_id
  接收者 ID  : ou_xxxxxxxxxxxx
```

然后让用户选择：

```
请选择操作：

1. 重新配置全部
2. 修改特定字段
3. 测试现有配置
```

- 用户选择 **1** → 跳转到**第三步**
- 用户选择 **2** → 跳转到**第二步b**
- 用户选择 **3** → 跳转到**第五步**

**如果配置不存在**，显示：

```
未检测到通知配置，将引导你完成首次配置。
```

然后进入**第三步**。

### 第二步b：修改特定字段

展示所有可编辑字段及当前值：

```
请选择要修改的字段（输入编号，多个用逗号分隔）：

1. App ID (当前: cli_xxxx...)
2. App Secret (当前: ****...****)
3. 接收者类型 (当前: open_id)
4. 接收者 ID (当前: ou_xxxx...)
```

根据用户选择的字段，跳转到对应的收集子步骤：
- 1 → 第四步a
- 2 → 第四步b
- 3 → 第四步c
- 4 → 第四步d

未选择的字段保留现有配置中的当前值。收集完所有选择的字段后，跳转到**第四步**。

### 第三步：Python 环境检查

```
检查 Python 环境...
```

1. 运行 `python3 --version`
2. 运行 `python3 -c "import requests; print(requests.__version__)"`

**均通过**：
```
Python 环境检查完成
  Python   : <version> ... OK
  requests : <version> ... OK
```

进入**第四步**。设置 `notificationType` 为 `"feishu"`。

**Python 未安装**：
```
Python 3 未安装。飞书通知需要 Python 3。
安装方式：brew install python3 (macOS)
```

询问用户是否继续或取消。

**requests 未安装**：
```
requests 库未安装。是否自动安装？(y/n)
```

如果是，运行 `pip3 install requests` 并验证。如果否，提示通知功能将不可用但继续。

### 第四步：收集飞书凭证

每个子步骤显示进度指示器。每次输入后，简要确认已收集的内容。

#### 第四步a：App ID

```
[Step 1/4] 飞书应用 App ID

请输入飞书应用的 App ID：

  格式    : cli_ 开头 + 16 位字母数字
  示例    : cli_a1b2c3d4e5f6g7h8
  获取方式 : 飞书开发者后台 → 凭证与基础信息 → App ID
```

**校验规则**：必须匹配 `^cli_[a-zA-Z0-9]{16}$`

校验失败时：
```
格式错误。App ID 应为 cli_ 开头加 16 位字母数字。请重新输入：
```

#### 第四步b：App Secret

```
[Step 2/4] 飞书应用 App Secret

请输入飞书应用的 App Secret：

  格式    : 32 位以上字母数字组合
  获取方式 : 飞书开发者后台 → 凭证与基础信息 → App Secret（点击查看）
```

**校验规则**：最少 32 个字符。

#### 第四步c：接收者类型

```
[Step 3/4] 通知接收者类型

通知发送给谁？

1. 我自己 — 需要 open_id
2. 群聊   — 需要 chat_id
```

#### 第四步d：接收者 ID

根据第四步c的选择：

**open_id**：
```
[Step 4/4] 接收者 Open ID

请输入你的 Open ID：

  格式    : ou_ 开头 + 字母数字
  示例    : ou_a1b2c3d4e5f6g7h8
  获取方式 : 通过飞书开放平台 API 获取用户信息
```

**校验规则**：必须匹配 `^ou_[a-zA-Z0-9]+$`

**chat_id**：
```
[Step 4/4] 群聊 Chat ID

请输入群聊 Chat ID：

  格式    : oc_ 开头 + 字母数字
  示例    : oc_a1b2c3d4e5f6g7h8
  获取方式 : 飞书群聊设置 → 群 ID
```

**校验规则**：必须匹配 `^oc_[a-zA-Z0-9]+$`

### 第五步：配置摘要与确认

显示所有待保存的值（App Secret 脱敏）：

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

- **保存并继续**：
  1. 读取现有 `~/.claude/settings.local.json`（如存在）
  2. 深度合并：保留所有现有字段，仅更新/添加通知相关字段
  3. 将合并后的配置写回 `~/.claude/settings.local.json`
  4. 运行 `chmod 600 ~/.claude/settings.local.json`
  5. 进入**第六步**

- **重新配置** → 返回**第四步**
- **取消** → 显示 `配置已取消。` 并退出

### 第六步：测试通知（可选）

```
配置已保存！

是否发送测试通知来验证配置？

1. 发送测试通知
2. 跳过
```

**如果用户选择"发送测试通知"**：

通过 Bash 运行：
```bash
echo '{"stop_reason":"completed","session_id":"test-setup"}' | python3 <plugin_root>/script/hooks/stop.py
```

其中 `<plugin_root>` 是插件目录路径（即本 SKILL.md 文件的上上级目录）。

**发送成功**（stderr 包含 "notification sent"）：
```
测试通知发送成功！请检查你的飞书消息。
如果收到了标题为"会话结束"的卡片消息，说明配置正确。
```

进入**第七步**。

**发送失败**：
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

- **重新配置凭证** → 跳转到**第四步a**
- **忽略并继续** → 进入**第七步**

**如果用户选择"跳过"**：进入**第七步**。

### 第七步：完成

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

## 配置格式

```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

## 校验规则

- **notificationType**：必须为 `"feishu"`
- **feishuAppId**：必须匹配正则 `^cli_[a-zA-Z0-9]{16}$`
- **feishuAppSecret**：最少 32 个字符
- **feishuReceiveId**：
  - 类型为 `"open_id"` 时：必须匹配正则 `^ou_[a-zA-Z0-9]+$`
  - 类型为 `"chat_id"` 时：必须匹配正则 `^oc_[a-zA-Z0-9]+$`
- **feishuReceiveIdType**：必须为 `"open_id"` 或 `"chat_id"`

## 错误处理

- 用户在任意步骤取消时：显示 `配置已取消。`
- 校验失败时：显示错误信息并允许重试
- 文件写入失败时：显示错误信息及排查步骤
- 合并配置时始终保留现有字段

## 安全须知

- 文件权限必须设置为 600（仅所有者可读写）
- 不得显示完整的 App Secret — 始终脱敏中间字符
- 保存前必须校验所有输入
