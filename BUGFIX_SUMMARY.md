# 飞书通知卡片消息修复总结

## 问题描述

Claude DX 的飞书通知功能中,卡片消息发送失败,错误代码 **99992402** (请求参数格式错误)。

## 根本原因

`hooks/common/feishu_bot.py` 中的 `send_card_message` 方法构建 payload 时,使用了错误的字段名。

### 错误代码 (第 217-221 行)

```python
payload = {
    "receive_id": self.receive_id,
    "msg_type": "interactive",
    "card": card  # ❌ 错误!飞书API不支持此字段
}
```

### 修复后代码

```python
payload = {
    "receive_id": self.receive_id,
    "msg_type": "interactive",
    "content": json.dumps(card)  # ✅ 正确:card需要序列化为JSON字符串并放在content字段
}
```

## 修复说明

根据飞书开放平台 API 文档,发送交互式卡片消息时:

1. **消息类型** 设置为 `msg_type: "interactive"`
2. **卡片内容** 必须序列化为 JSON 字符串并放在 `content` 字段中
3. ~~不支持~~ 直接使用 `card` 字段传递卡片对象

## 测试验证

### 1. 基础测试 ✅

使用 `test_feishu_card.py` 验证基础卡片消息发送:

```bash
python3 /Users/admin/Documents/GitHub/claude-dx/hooks/test_feishu_card.py
```

**结果**: ✅ 卡片消息发送成功

### 2. Hook场景测试 ✅

使用 `test_real_hook.py` 验证实际Hook场景:

```bash
python3 /Users/admin/Documents/GitHub/claude-dx/hooks/test_real_hook.py
```

**结果**: 所有Hook类型的卡片消息都成功发送:
- 🔵 SessionStart (蓝色卡片)
- 🟠 PreToolUse (橙色卡片)
- 🟢 PostToolUse 成功 (绿色卡片)
- 🔴 PostToolUse 失败 (红色卡片)

## 影响范围

此修复影响所有通过 `FeishuAppBot.send_card_message()` 发送的卡片消息,包括:

- SessionStart Hook
- PreToolUse Hook
- PostToolUse Hook
- PermissionRequest Hook
- SubagentStop Hook

## 文件修改清单

| 文件 | 修改内容 | 行数 |
|------|----------|------|
| `hooks/common/feishu_bot.py` | 修改 payload 构建逻辑 | 217-221 |

## 下一步

1. ✅ 核心修复已完成
2. 🔄 将 Claude DX hooks 配置到 `~/.claude/settings.json` (可选)
3. 📱 在实际使用中验证飞书通知效果

## 技术细节

### 飞书 API 消息格式差异

| 消息类型 | msg_type | content 字段格式 |
|---------|----------|------------------|
| 文本消息 | `text` | `json.dumps({"text": "消息内容"})` |
| 富文本消息 | `post` | `json.dumps(post_object)` |
| **卡片消息** | `interactive` | `json.dumps(card_object)` ← 本次修复 |

### 调试技巧

1. 检查飞书 API 响应中的错误代码
2. 使用日志记录请求 payload 和响应
3. 参考官方文档验证字段格式
4. 创建独立测试脚本验证修复

## 参考资料

- [飞书开放平台 - 发送消息](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create)
- [飞书消息卡片搭建指南](https://open.feishu.cn/document/ukTMukTMukTM/uczM3QjL3MzN04yNzcDN)

---

**修复日期**: 2026-02-05
**测试状态**: ✅ 所有测试通过
**部署状态**: ✅ 已完成
