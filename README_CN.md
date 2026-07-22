# Agent Constraint System (ACS)

> AI 编码 Agent 的生产级安全约束层。8 个 Agent、1 个核心、1 条命令。

## 安装

| 方式 | 命令 |
|------|------|
| **npm** | `npm install -g github:kamanager2012/agent-constraint-system` |
| **curl** | `curl -fsSL https://raw.githubusercontent.com/kamanager2012/agent-constraint-system/main/install-remote.sh \| bash` |
| **GitHub** | `git clone https://github.com/kamanager2012/agent-constraint-system.git && cd agent-constraint-system && ./install.sh` |

安装后：

```bash
acs install          # 自动检测 Agent，选单勾选安装
acs status           # 查看保护状态
```

## 支持的 Agent

| Agent | 适配器 | 状态 |
|-------|--------|------|
| Claude Code | ACS | 完整部署（22 文件） |
| Codex CLI (OpenAI) | CACS | Python 适配器 |
| Gemini CLI (Google) | GACS | Python 适配器 |
| Cursor | CrACS | Shell 启用脚本 |
| Qoder CN | QACS | Python 适配器 |
| Hermes Agent | HACS | Python 适配器 |
| OpenCode | OACS | TypeScript 插件 |
| CodeBuddy Code | BACS | 复用 ACS hooks |
| Grok Build (xAI) | XACS | 无文件系统 hook |

## 拦截内容

| 类别 | 示例 |
|------|------|
| 危险 Bash | `rm -rf /`、`kill -9`、`mkfs`、`dd if=/dev/`、`chmod 777 /etc`、curl-pipe-shell |
| 破坏性 Git | `git reset --hard`、`git restore --worktree -- .`、`git push --force`、`git clean -fdx` |
| 系统写入 | 任何对 `/etc/`、`/usr/`、`/bin/`、`/boot/`、`/sys/` 等 14 个禁止根目录的写入 |
| 自保护 | Agent 无法修改约束系统自身文件 |

## CLI 命令

| 命令 | 作用 |
|------|------|
| `init` | 创建运行时目录（首次必执行） |
| `status` | 显示违规、审计、完整性状态 |
| `unlock --confirm` | 清除违规并解锁（需人工确认） |
| `reset --force --confirm` | 完全重置状态（需人工确认） |

## 安全设计

- **不自启** — 运行时目录必须显式 `init`；未初始化时 hook 静默跳过
- **解锁需确认** — `--confirm` 标志防止 Agent 自主绕过
- **滑动窗口** — 违规累积；超阈值触发锁定
- **完整性链** — SHA-256 哈希链检测约束文件是否被篡改
- **自保护** — Agent 无法修改自身守卫

## 架构

```
┌──────────────────────────────┐
│  acs_core/     共享核心      │
│  guard.py      Bash+Git 模式 │
│  paths.py      禁止根检测    │
│  violations.py 滑动窗口+锁   │
│  audit.py      JSONL 审计    │
│  structural.py 代码结构验证  │
└──────────┬───────────────────┘
           │
    ┌──────┼──────┬──────┬──────┬──────┬──────┬──────┐
    ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
 Claude  Codex  Gemini Cursor Qoder  Hermes Open  CodeBuddy
  ACS    CACS   GACS   CrACS  QACS   HACS   OACS   BACS
 Python Python Python Shell  Python Python TS     复用ACS

```

## 开源许可

MIT — 详见 `LICENSE` 文件。

---

[English](./README.md)
