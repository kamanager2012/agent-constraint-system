# Agent Constraint System (ACS)

Agent 不信任。所有 Write / Edit / Bash 必须经过治理层。

## 当前版本：v1.2.0

| 组件 | 位置 |
|------|------|
| 代码 | `~/.claude/hooks/` |
| 状态 | `~/.claude/runtime/` |
| 项目 | `~/agent-constraint-system/` |

## Agent 进入第一件事

```
PROJECT.md
ARCHITECTURE.md
memory/agent-onboarding.md
context/CURRENT_STATE.md
context/NEXT_TASK.md
```

## 目录

```
~/agent-constraint-system/
├── PROJECT.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── current → versions/v1.1.0
├── hooks → ~/.claude/hooks
├── runtime → ~/.claude/runtime
│
├── memory/          ← Agent 记忆（onboarding / known-bugs / pitfalls）
├── context/         ← CURRENT_STATE / NEXT_TASK / ROADMAP
├── modules/         ← 每个模块一个文件
├── decisions/       ← ADR
├── design/          ← 功能设计
├── analysis/        ← 分析报告
├── reports/         ← 升级报告
├── governance/      ← 治理文档
├── runbooks/        ← 操作手册
├── status/          ← 临时状态
│
├── versions/        ← 代码快照（每版本一个目录）
└── archive/         ← audits / experiments / deprecated
```

## 快速命令

```bash
python3 ~/.claude/hooks/acs_lite.py status              # 状态
~/.claude/hooks/acs_task.sh <id> <dirs>                  # 初始化 scope
```
