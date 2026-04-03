# Claude DX

Claude Code 插件，提供飞书实时通知和 Java/Spring Boot 开发工作流增强。

## 功能

### Hooks - 飞书实时通知

通过 Hooks 在 Claude Code 运行时发送飞书应用机器人通知：

| Hook | 说明 |
|------|------|
| Notification | 通用通知 |
| PermissionRequest | 权限请求通知 |
| Stop | 会话结束通知 |

### Skills - 开发工作流

| Skill | 说明 |
|-------|------|
| `/dev-pipeline` | 开发交付闭环（计划→拆解→编码→编译→推送→交付） |
| `/git-push` | 自动 commit + push 到远程分支 |
| `/setup` | 配置向导 |
| `/java-coding-standards` | Java 编码规范（基于阿里巴巴 Java 开发手册） |
| `/springboot-patterns` | Spring Boot 架构模式 |
| `/mybatis-plus-patterns` | MyBatis-Plus 持久化模式 |

## 安装

```bash
# 添加市场
/plugin marketplace add wsong001/claude-dx

# 安装插件
/plugin install claude-dx@claude-dx
```

## 配置

安装后运行 `/setup` 配置飞书通知，或手动编辑 `~/.claude/settings.local.json`：

```json
{
  "notificationType": "feishu",
  "feishuAppId": "cli_xxxxxxxxxxxxxx",
  "feishuAppSecret": "your-app-secret",
  "feishuReceiveId": "ou_xxxxxxxxxx",
  "feishuReceiveIdType": "open_id"
}
```

## 许可证

MIT License
