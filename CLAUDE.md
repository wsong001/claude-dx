# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude DX 是一个 Claude Code 插件，通过 Hooks 系统在 Claude Code 运行时发送飞书应用机器人实时通知。

## Architecture

### Plugin System

- `.claude-plugin/plugin.json` — 插件清单，声明版本、skills 目录
- `.claude-plugin/marketplace.json` — Marketplace 发布配置
- `hooks/hooks.json` — Hook 事件绑定配置，将 Claude Code 事件映射到 Python 脚本

### Hook Scripts (`script/hooks/`)

所有 hook 脚本共享同一模式：从 stdin 读取 JSON → 处理 → 将原始 JSON 写回 stdout。

- `lib.py` — 合并的通用库，包含所有共享模块：
  - `Config` 类 — 配置加载（环境变量 > `settings.local.json` > `settings.json` > 默认值）
  - `StderrLogger` — 日志输出到 stderr（不干扰 hook 的 stdin/stdout 协议）
  - `FeishuTokenManager` — 飞书 tenant_access_token 获取与缓存
  - `FeishuAppBot` — 飞书卡片消息发送（含重试和限流处理）
  - `filter_sensitive_info()` — 敏感信息正则过滤
  - `format_dict_summary()` / `get_session_id()` — 格式化工具
- `notification.py` — Notification hook（通用通知）
- `permission_request.py` — PermissionRequest hook（权限请求通知）
- `stop.py` — Stop hook（会话结束通知）

### Skills (`skills/`)

Skills 是纯 Markdown 文件，由 Claude Code 解释执行：

- `setup/SKILL.md` — `/setup` 配置向导（飞书凭证收集、配置验证）
- `git-push/SKILL.md` — `/git-push` 自动 commit + push 到远程
- `dev-pipeline/SKILL.md` — `/dev-pipeline` 开发交付闭环（计划→拆解→编码→编译→推送→交付）
- `java-coding-standards/SKILL.md` — Java 编码规范（基于阿里巴巴 Java 开发手册）
- `springboot-patterns/SKILL.md` — Spring Boot 架构模式
- `mybatis-plus-patterns/SKILL.md` — MyBatis-Plus 持久化模式（基于阿里巴巴 ORM 映射规约）

### Configuration

用户配置存储在 `~/.claude/settings.local.json`，关键字段：

| 字段 | 说明 |
|------|------|
| `notificationType` | `"feishu"` |
| `feishuAppId` | 飞书应用 ID (`cli_xxx`) |
| `feishuAppSecret` | 飞书应用密钥 |
| `feishuReceiveId` | 接收者 ID |
| `feishuReceiveIdType` | `"open_id"` 或 `"chat_id"` |

## Development

### Prerequisites

- Python 3.7+
- `pip3 install requests`

### Loading the Plugin

```bash
claude --plugin-dir /path/to/claude-dx
```

### Testing Hooks Manually

```bash
# 测试 Stop hook
echo '{"stop_reason":"completed","session_id":"test-123"}' | python3 script/hooks/stop.py

# 测试 Notification hook
echo '{"notification_type":"info","message":"test","level":"info"}' | python3 script/hooks/notification.py

# 测试 PermissionRequest hook
echo '{"permission_type":"executeCommand","permission_data":{}}' | python3 script/hooks/permission_request.py
```

### Key Convention

所有 hook 脚本必须：
1. 从 `sys.stdin` 读取 JSON
2. 将原始输入 JSON 写回 `sys.stdout`（保证 hook 链不中断）
3. 日志输出到 `sys.stderr`
4. 异常时 `sys.exit(0)`（不阻塞 Claude Code）
