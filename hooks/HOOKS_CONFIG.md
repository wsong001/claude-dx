# Claude DX Hooks 配置说明

## 当前配置

### ✅ 已启用的 Hooks

| Hook 类型 | 触发时机 | 通知颜色 | 频率 |
|----------|---------|---------|------|
| **Notification** | 系统发送通知时 | 🟡/🔵/🟢/🟠 (取决于类型) | 低-中 |
| **Stop** | Claude 完成响应时 | 🟢/🟡/🔴 (取决于状态) | 低 |

#### Notification 支持的通知类型:
- 🔐 `permission_prompt` - 权限请求提示 (黄色)
- 💤 `idle_prompt` - 空闲等待输入 (蓝色)
- ✅ `auth_success` - 认证成功 (绿色)
- ❓ `elicitation_dialog` - 需要用户输入 (橙色)

#### Stop 支持的停止类型:
- ✅ `normal` - 正常完成 (绿色)
- ⏸️ `interrupted` - 用户中断 (黄色)
- ❌ `error` - 异常停止 (红色)

### 🚫 已禁用的 Hooks

以下 hooks 已被禁用,因为触发过于频繁或暂不需要:

| Hook 类型 | 触发时机 | 通知颜色 | 频率 | 禁用原因 |
|----------|---------|---------|------|---------|
| PermissionRequest | 需要用户权限时 | 🟡 黄色 | 低-中 | 与 Notification(permission_prompt) 功能重叠 |
| SessionStart | 会话开始时 | 🔵 蓝色 | 低 | 每次会话开始通知一次,可能不需要 |
| PreToolUse | 每次工具执行前 | 🟠 橙色 | **极高** | 每个工具调用都触发 |
| PostToolUse | 每次工具执行后 | 🟢/🔴 绿色/红色 | **极高** | 每个工具调用都触发 |
| SubagentStop | 子代理停止时 | 🟣 紫色 | 中 | 使用子代理时频繁 |

## 如何启用/禁用 Hooks

### 启用已禁用的 Hook

如果你想重新启用某个 hook(例如 SessionStart):

1. 打开 `hooks/hooks.json`
2. 将对应的配置从 `_disabled_hooks` 移回 `hooks` 字段:

```json
{
  "hooks": {
    "PermissionRequest": [...],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/entry_points/session_start_hook.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### 禁用某个 Hook

1. 将对应的配置从 `hooks` 移到 `_disabled_hooks`
2. 或者直接删除该配置

## 推荐配置方案

### 方案 1: 关键事件通知(当前方案) ⭐

**适合**: 关注会话的关键节点(通知和停止),不被频繁打扰

```json
{
  "hooks": {
    "Notification": [...],
    "Stop": [...]
  }
}
```

**触发场景**:
- 系统需要权限时
- Claude 等待输入时
- 认证成功时
- 会话正常/异常结束时

### 方案 2: 完整会话追踪

**适合**: 需要完整监控会话的开始和结束

```json
{
  "hooks": {
    "SessionStart": [...],
    "Notification": [...],
    "Stop": [...]
  }
}
```

**触发场景**:
- 会话开始时
- 系统通知时
- 会话结束时

### 方案 3: 最小通知

**适合**: 只关心会话完成,不需要过程通知

```json
{
  "hooks": {
    "Stop": [...]
  }
}
```

**触发场景**:
- 仅当会话结束时通知

### 方案 4: 完整监控(仅用于调试)

**适合**: 开发调试阶段,需要看到所有活动

```json
{
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "PermissionRequest": [...],
    "SubagentStop": [...]
  }
}
```

⚠️ **警告**: 方案 4 会在飞书中产生大量通知,不推荐日常使用!

## Hook 详细说明

### PermissionRequest ✅ (已启用)

**触发**: 当 Claude Code 需要执行敏感操作时(如修改文件、运行命令)

**通知内容**:
- 请求的权限类型
- 工具名称和参数
- 会话ID

**为什么保留**:
- 触发频率低
- 安全相关,重要
- 帮助了解 Claude Code 的操作

### SessionStart 🚫 (已禁用)

**触发**: 每次启动新的 Claude Code 会话

**通知内容**:
- 会话ID
- 工作目录
- Git仓库状态
- 启动时间

**禁用原因**: 频率低但可能不需要每次都通知

### PreToolUse 🚫 (已禁用)

**触发**: 每次工具执行前(Read、Write、Edit、Bash 等)

**通知内容**:
- 工具名称
- 输入参数
- 会话ID

**禁用原因**: **极度频繁** - 一个简单任务可能触发几十次

### PostToolUse 🚫 (已禁用)

**触发**: 每次工具执行后

**通知内容**:
- 工具名称
- 执行结果(成功/失败)
- 输出摘要
- 执行耗时

**禁用原因**: **极度频繁** - 与 PreToolUse 一样频繁

### SubagentStop 🚫 (已禁用)

**触发**: 子代理(如 planner、code-reviewer 等)完成任务时

**通知内容**:
- 子代理类型
- 执行结果
- 会话ID

**禁用原因**: 使用 Task 工具时会频繁触发

## 自定义配置

你可以根据需要自定义通知的过滤条件。例如,只监控特定工具:

```json
{
  "PostToolUse": [
    {
      "matcher": "Bash|Edit|Write",  // 只监控这些工具
      "hooks": [...]
    }
  ]
}
```

## 测试配置

修改配置后,可以使用测试脚本验证:

```bash
# 测试基础卡片消息
python3 /Users/admin/Documents/GitHub/claude-dx/hooks/test_feishu_card.py

# 测试所有 hook 场景
python3 /Users/admin/Documents/GitHub/claude-dx/hooks/test_real_hook.py
```

## 故障排查

如果通知没有发送:

1. **检查配置**: 确认 `~/.claude/settings.local.json` 中的飞书配置正确
2. **检查 token**: 查看 `~/.feishu_token_cache` 是否存在且有效
3. **查看日志**: 检查日志文件中的错误信息
4. **测试连接**: 运行测试脚本验证飞书 API 连接

## 相关文件

- `hooks/hooks.json` - Hook 配置文件(本文件)
- `~/.claude/settings.local.json` - 飞书应用凭证配置
- `~/.feishu_token_cache` - Token 缓存文件
- `hooks/common/feishu_bot.py` - 飞书 API 封装

---

**最后更新**: 2026-02-05
**当前方案**: 方案 1 - 关键事件通知 (Notification + Stop)
