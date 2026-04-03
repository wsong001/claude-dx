---
name: git-push
description: Push local changes to git remote branch
---

# Push - Git Push Command

Push local changes to git remote branch with automatic commit.

## Instructions

When user runs `/push`, follow these steps:

### Step 0: Handle Plan Mode

**CRITICAL**: If currently in Plan Mode, automatically exit it using `ExitPlanMode` tool before proceeding. Do NOT ask the user for confirmation - push commands require write access to the repository.

### Step 1: Check Git Status

Run `git status` to check current branch and changes.

Display the status to user:

```
📋 Git 状态
```

Show:
- Current branch
- Modified files
- Untracked files (if any)

### Step 2: Auto-Generate Commit Message

Automatically analyze git diff to generate an intelligent commit message.

**Analysis Process**:

1. Run `git diff --cached --stat` to see changed files
2. Run `git diff --cached` to see actual changes
3. Categorize changes based on:
   - **feat**: New files/functions, feature additions
   - **fix**: Keywords like fix/bug/修复/solve
   - **docs**: .md/.txt documentation files
   - **test**: Test files or test-related changes
   - **chore**: Config files, dependencies, package updates
   - **refactor**: Code restructuring without behavior change

4. Generate concise commit message in format: `<type>: <description>`

**Display to user**:
```
📝 自动生成的提交消息：
<generated_commit_message>
```

### Step 3: Execute Git Operations

Automatically execute the following operations:

1. **Stage all changes**: `git add .`
2. **Commit with message**: `git commit -m "<message>"`
3. **Push to remote**: `git push`

Show progress:
```
⏳ 正在推送...
  1. 暂存文件...
  2. 提交更改...
  3. 推送到远程...
```

### Step 4: Display Result

Show success or error message:

**Success**:
```
╔════════════════════════════════════════════════════════════╗
║  ✅ 推送成功！                                             ║
╚════════════════════════════════════════════════════════════╝

📝 Commit: <commit_hash>
🌿 分支: <branch_name>
🔗 远程: <remote_url>
```

**Error**:
```
❌ 推送失败

<error_details>

可能的原因：
  - 网络连接问题
  - 远程分支冲突
  - 权限不足

建议：先运行 git pull 拉取远程更新
```

## Error Handling

- If no changes detected: "⚠️ 没有需要提交的更改"
- If commit fails: Show git error message, suggest fixing conflicts
- If push fails: Show error, suggest `git pull --rebase`
- Always preserve user intent - don't force push without explicit confirmation

## Commit Message Conventions

Support conventional commit format:

| Type | Description | Example |
|------|-------------|---------|
| feat | 新功能 | feat: 添加用户登录 |
| fix | 修复问题 | fix: 修复登录超时 |
| docs | 文档更新 | docs: 更新 README |
| style | 代码格式 | style: 统一代码风格 |
| refactor | 重构 | refactor: 优化认证流程 |
| test | 测试相关 | test: 添加单元测试 |
| chore | 构建/工具 | chore: 更新依赖版本 |
