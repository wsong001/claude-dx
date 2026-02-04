# Claude DX Hooks 开发文档

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────┐
│                   Claude Code                        │
│                                                      │
│  ┌────────────┐  JSON   ┌──────────────────────┐   │
│  │ Hook Event │ ──────> │ Hook Entry Script    │   │
│  └────────────┘         └──────────────────────┘   │
│                                │                     │
│                                ▼                     │
│                         ┌──────────────┐            │
│                         │   Handler    │            │
│                         └──────────────┘            │
│                                │                     │
│                      ┌─────────┴─────────┐          │
│                      ▼                   ▼          │
│              ┌──────────────┐    ┌──────────────┐  │
│              │  Feishu Bot  │    │VSCode Notifier│  │
│              └──────────────┘    └──────────────┘  │
│                      │                   │          │
└──────────────────────┼───────────────────┼──────────┘
                       │ HTTPS             │ osascript
                       ▼                   ▼
                ┌──────────────┐    ┌──────────────┐
                │ Feishu API   │    │macOS系统通知  │
                └──────────────┘    └──────────────┘
```

**通知渠道（二选一）**:
- **飞书通知**: 使用 Feishu Bot 发送卡片消息到飞书
- **VSCode 通知**: 使用 VSCode Notifier 发送 macOS 系统通知

### 数据流

1. **Claude Code** 触发Hook事件
2. **Entry Script** 从stdin读取JSON
3. **Handler** 处理数据并调用Feishu Bot
4. **Feishu Bot** 发送HTTP请求
5. **Entry Script** 输出原始JSON到stdout (pass-through)
6. **Claude Code** 继续执行

## Hook类型

### 1. SessionStart

**触发时机:** Claude Code会话启动时

**输入数据:**
```json
{
  "session_id": "abc123",
  "timestamp": "2024-02-04T12:00:00Z",
  "cwd": "/path/to/project",
  "git_repo": true,
  "git_branch": "main",
  "user": "username"
}
```

**消息格式:**
- 颜色: 蓝色 (#1890FF)
- 标题: "🎯 会话开始 | Session Start"
- 内容: 会话ID、工作目录、Git状态

### 2. PreToolUse

**触发时机:** 工具执行前

**输入数据:**
```json
{
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la",
    "description": "List files"
  },
  "timestamp": "2024-02-04T12:00:00Z"
}
```

**消息格式:**
- 颜色: 橙色 (#FA8C16)
- 标题: "⚙️ 工具执行前 | Pre Tool Use"
- 内容: 工具名称、输入参数摘要

**特殊处理:**
- Bash: 显示命令
- Read: 显示文件路径
- Write/Edit: 显示文件路径和内容长度
- Grep/Glob: 显示搜索模式

### 3. PostToolUse

**触发时机:** 工具执行后

**输入数据:**
```json
{
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_result": {
    "output": "...",
    "exit_code": 0
  },
  "duration": 1234,
  "timestamp": "2024-02-04T12:00:00Z"
}
```

**消息格式:**
- 颜色: 成功=绿色 (#52C41A), 失败=红色 (#F5222D)
- 标题: "✓ 工具执行后 | Post Tool Use" 或 "✗ 工具执行后"
- 内容: 执行状态、输出摘要、耗时

**状态判断:**
1. 检查 `tool_result.error`
2. 检查 `tool_result.exit_code`
3. 检查 `tool_result.status`

### 4. PermissionRequest

**触发时机:** 需要用户授权时

**输入数据:**
```json
{
  "session_id": "abc123",
  "permission_type": "file_write",
  "tool_name": "Write",
  "resource": "/path/to/file",
  "action": "Create new file",
  "description": "...",
  "timestamp": "2024-02-04T12:00:00Z"
}
```

**消息格式:**
- 颜色: 黄色 (#FAAD14)
- 标题: "🔒 权限请求 | Permission Request"
- 内容: 权限类型、资源、操作说明

### 5. SubagentStop

**触发时机:** 子代理执行完成时

**输入数据:**
```json
{
  "session_id": "abc123",
  "agent_type": "Explore",
  "agent_name": "explore-agent",
  "status": "completed",
  "summary": "...",
  "result": {...},
  "turns": 5,
  "duration": 12345,
  "tokens_used": 8000,
  "timestamp": "2024-02-04T12:00:00Z"
}
```

**消息格式:**
- 颜色: 紫色 (#722ED1)
- 标题: "🤖 子代理停止 | Subagent Stop"
- 内容: 代理名称、完成状态、执行摘要、统计信息

## 敏感信息过滤

### 过滤模式

自动过滤包含以下关键词的字段:
- `api_key`, `api-key`
- `secret`
- `password`
- `token`
- `auth`
- `credential`
- `private_key`, `private-key`

### 过滤方式

```python
# 匹配 key: value 或 "key": "value" 格式
pattern = r'(["']?api_key["']?\s*[:=]\s*)([^,\s\]}}]+)'
replacement = r'\1***'
```

### 长度限制

- **参数摘要**: 最大300字符
- **输出摘要**: 最大500字符
- **文件内容**: 不发送完整内容,仅显示长度

## 错误处理

### 设计原则

**失败不影响主流程** - 所有异常必须被捕获,Hook失败不应阻塞Claude执行

### 错误处理层次

1. **Entry Script层**
   - 捕获JSON解析错误
   - 捕获Handler异常
   - 始终返回exit code 0
   - 输出原始JSON到stdout (pass-through)

2. **Handler层**
   - 捕获处理逻辑异常
   - 记录错误到stderr
   - 不抛出异常

3. **Feishu Bot层**
   - 捕获网络错误
   - 捕获API错误
   - 实现重试机制
   - 返回bool而非抛出异常

### 示例

```python
try:
    # 业务逻辑
    handler.process(input_data)
except Exception as e:
    # 记录但不抛出
    logger.error(f"Error: {e}", exc_info=e)
finally:
    # 总是成功退出
    sys.exit(0)
```

## 重试机制

### 策略

- **最大重试次数**: 3次
- **初始延迟**: 1秒
- **退避策略**: 线性增长 (delay * attempt)
- **重试触发**: HTTP 429 (限流), Timeout

### 实现

```python
for attempt in range(1, max_retries + 1):
    try:
        response = requests.post(...)
        if response.status_code == 429:
            time.sleep(retry_delay * attempt)
            continue
        return handle_response(response)
    except Timeout:
        if attempt < max_retries:
            time.sleep(retry_delay)
            continue
```

## 配置加载

### 通知渠道选择

通过 `notificationChannel` 配置项选择通知方式（**二选一**）：

- `"feishu"` (默认) - 飞书通知
- `"vscode"` - VSCode 系统通知（仅 macOS）

### 优先级

配置的加载顺序:

1. 环境变量
   - 通用: `NOTIFICATION_CHANNEL`
   - 飞书: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_RECEIVE_ID`, `FEISHU_RECEIVE_ID_TYPE`
   - VSCode: `VSCODE_NOTIFICATION_SOUND`, `VSCODE_NOTIFICATION_TYPES`
2. `~/.claude/settings.local.json`
   - 通用: `notificationChannel`
   - 飞书: `feishuAppId`, `feishuAppSecret`, `feishuReceiveId`, `feishuReceiveIdType`
   - VSCode: `vscodeNotificationSound`, `vscodeNotificationTypes`
3. `~/.claude/settings.json` - 同上字段(备用)
4. 默认值:
   - `notificationChannel`: `"feishu"` (向后兼容)
   - `feishuReceiveIdType`: `"open_id"`
   - `vscodeNotificationSound`: `true`
   - `vscodeNotificationTypes`: `["Stop", "Notification"]`

### 配置示例

**飞书模式**:
```json
{
  "notificationChannel": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret-here",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

**VSCode 模式**:
```json
{
  "notificationChannel": "vscode",
  "vscodeNotificationSound": true,
  "vscodeNotificationTypes": ["Stop", "Notification"]
}
```

### 实现

```python
def _load_config(self, env_key: str, config_key: str, default: Optional[str] = None):
    # 1. 环境变量(最高优先级)
    if value := os.getenv(env_key):
        return value

    # 2. local配置
    local_config = Path.home() / ".claude/settings.local.json"
    if local_config.exists():
        data = json.load(local_config.open())
        if value := data.get(config_key):
            return value

    # 3. 全局配置
    global_config = Path.home() / ".claude/settings.json"
    if global_config.exists():
        data = json.load(global_config.open())
        if value := data.get(config_key):
            return value

    # 4. 默认值
    return default
```

### Token缓存

飞书应用Token自动缓存到 `~/.feishu_token_cache`:
- **有效期**: 2小时
- **自动刷新**: 提前5分钟刷新
- **文件权限**: 0600 (仅所有者可读写)
- **格式**: JSON (`{"token": "...", "expire_time": 1234567890}`)

## 日志

### 输出位置

**所有日志必须输出到stderr** - stdout用于JSON pass-through

### 日志级别

- **DEBUG**: 详细调试信息 (默认关闭)
- **INFO**: 正常操作信息 (默认级别)
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 配置

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG
```

## 开发指南

### 添加新Hook类型

1. 创建处理器 `hooks/handlers/new_hook.py`:
   ```python
   from .base_handler import BaseHandler

   class NewHookHandler(BaseHandler):
       def validate_input(self, input_data):
           return "required_field" in input_data

       def send_notification(self, input_data):
           # 实现通知逻辑
           pass
   ```

2. 创建入口脚本 `hooks/entry_points/new_hook.py`:
   ```python
   from handlers.new_hook import NewHookHandler

   def main():
       input_data = json.load(sys.stdin)
       handler = NewHookHandler()
       handler.process(input_data)
       json.dump(input_data, sys.stdout)
       sys.exit(0)
   ```

3. 在 `hooks/hooks.json` 中注册:
   ```json
   {
     "NewHook": [{
       "hooks": [{
         "type": "command",
         "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/entry_points/new_hook.py",
         "timeout": 10
       }]
     }]
   }
   ```

### 测试新Hook

```bash
echo '{"test":"data"}' | python3 hooks/entry_points/new_hook.py
```

### 调试技巧

1. **增加日志级别**:
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. **查看stderr输出**:
   ```bash
   python3 hook.py 2>&1 | grep ERROR
   ```

3. **测试飞书消息**:
   ```python
   from hooks.common.feishu_bot import FeishuAppBot
   from hooks.common.config import config

   bot = FeishuAppBot(
       config.app_id,
       config.app_secret,
       config.receive_id,
       config.receive_id_type
   )
   bot.send_card_message("Test", "Content", "blue")
   ```

4. **测试Token获取**:
   ```python
   from hooks.common.feishu_bot import FeishuTokenManager
   from pathlib import Path

   tm = FeishuTokenManager(app_id, app_secret, Path.home() / ".feishu_token_cache")
   token = tm.get_token()
   print(f"Token: {token[:20]}...")
   ```

## 性能优化

### 当前实现

- **超时时间**: 10秒
- **消息大小**: 参数300字符, 输出500字符
- **重试次数**: 3次

### 潜在优化 (MVP2+)

- 消息队列 - 异步发送,避免阻塞
- 批量发送 - 合并多个通知
- 缓存 - 避免重复发送相同消息
- 压缩 - 减少网络传输

## 安全考虑

### 已实现

- ✅ 敏感信息正则过滤
- ✅ 文件内容不发送
- ✅ 参数长度限制
- ✅ 异常隔离

### 建议

- ⚠️ 不要将App Secret和Token缓存文件提交到Git
- ⚠️ 使用 `settings.local.json` 而非 `settings.json`
- ⚠️ 定期更换App Secret
- ⚠️ 限制飞书应用权限范围
- ⚠️ 仅授权必要的接收者(用户或群聊)

## 飞书应用机器人 vs 自定义机器人

### 核心差异

| 维度 | 自定义机器人(Webhook) | 应用机器人(App Bot) |
|------|---------------------|---------------------|
| 认证方式 | Webhook URL | App ID + App Secret + Token |
| API调用 | POST到Webhook | POST到开放API + Bearer Token |
| 接收者 | 固定群聊 | 可配置(用户/群聊) |
| Token管理 | 无需 | 需要获取和缓存 |
| 权限控制 | 无 | 需要申请和审核 |
| 适用场景 | 简单群聊通知 | 企业应用集成 |

### MVP1实现选择

Claude DX使用**应用机器人**模式,因为:
- ✅ 更灵活的接收者配置(个人/群聊)
- ✅ 更好的权限控制
- ✅ 符合企业应用规范
- ✅ 支持更多API能力扩展

## VSCode 通知配置

### 系统要求

- macOS 10.10+ (支持 AppleScript)
- 系统通知权限已启用

### 配置说明

**vscodeNotificationSound** (boolean, 默认: true)
- 是否播放通知音效
- 音效映射：
  - `info` → Glass
  - `success` → Hero
  - `warning` → Ping
  - `error` → Basso

**vscodeNotificationTypes** (array, 默认: `["Stop", "Notification"]`)
- 启用通知的 Hook 类型
- 可选值：`"Stop"`, `"Notification"`, `"SessionStart"`, `"PreToolUse"`, `"PostToolUse"`, `"PermissionRequest"`, `"SubagentStop"`

### 通知格式

**Stop Hook**:
- ✅ 正常完成: "Claude Complete" (success/green)
- ⚠️ 错误停止: "Claude Session Error" (error/red)
- ⏸️ 用户中断: "Claude Interrupted" (warning/yellow)
- 包含统计信息: 耗时、回合数、Token 数

**Notification Hook**:
- 🔐 权限请求: "Permission Required" (warning)
- 💤 空闲等待: "Claude Waiting" (info)
- ✅ 认证成功: "Authentication Success" (success)
- ❓ 需要输入: "Input Required" (warning)

### 故障排除

**通知不显示**:
1. 检查系统通知权限: 系统设置 → 通知 → Script Editor → 允许通知
2. 检查配置: `cat ~/.claude/settings.local.json | jq .notificationChannel`
3. 检查 Hook 类型: `cat ~/.claude/settings.local.json | jq .vscodeNotificationTypes`
4. 手动测试: `osascript -e 'display notification "test"'`

**常见错误**:
- `osascript not found`: 非 macOS 系统，请使用飞书通知
- `Permission denied`: 系统通知权限未开启

### 技术实现

VSCode 通知使用 macOS 原生技术栈：
- **通知发送**: `osascript` + AppleScript (`display notification`)
- **文本清理**: 转义特殊字符 (`\`, `"`, `\n`, `\r`, `\t`)
- **错误隔离**: 所有错误被捕获，不影响 Claude 执行

## 参考资源

- [Claude插件开发文档](https://docs.anthropic.com/claude-code/plugins)
- [飞书应用机器人API](https://open.feishu.cn/document/server-docs/im-v1/message/create)
- [飞书Token获取](https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal)
- [Hook规范](https://github.com/anthropics/claude-code/docs/hooks)
- [macOS AppleScript 通知](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
