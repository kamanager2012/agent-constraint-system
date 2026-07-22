# Agent Constraint System (ACS)

> A cross-agent runtime safety layer for autonomous coding agents.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green.svg)](https://python.org)

## At a Glance

ACS prevents coding agents from executing dangerous commands, modifying protected files, or circumventing safety constraints — using both pattern matching (Level 1) and asset-aware context (Level 2).

| Level | Scenarios | Pass Rate |
|-------|-----------|-----------|
| Level 1 (Pattern) | 105 | 91.4% |
| Level 2 (Asset) | 6 | 100% |
| Level 3 (Trajectory) | 6 | 100% |

*FP Rate: 0% | Bypass Resistance: 50% | Self-protect: runtime_required*

```bash
cd benchmarks && python3 runner.py           # Level 1: pattern matching
cd benchmarks/level2 && python3 runner.py    # Level 2: asset-aware tri-state gate
cd benchmarks/level3 && python3 runner.py    # Level 3: trajectory safety
```

## Supported Agents

| Agent | Adapter | Status |
|-------|---------|--------|
| **Codex CLI** (OpenAI) | [CACS](docs/codex-integration.md) | Python adapter |
| **Claude Code** (Anthropic) | ACS | Full deployment (22 files) |
| **Gemini CLI** (Google) | GACS | Python adapter |
| **Cursor** | CrACS | Shell bootstrap |
| **OpenCode** | OACS | TypeScript plugin |
| **CodeBuddy Code** | BACS | Reuses ACS hooks |
| **Qoder CN** | QACS | Python adapter |
| **Hermes Agent** | HACS | Python adapter |

## What ACS Blocks

| Category | Examples |
|----------|---------|
| **Dangerous Bash** | `rm -rf /`, `kill -9`, `mkfs`, `dd`, `chmod 777 /etc`, fork bombs, `curl\|sh` |
| **Destructive Git** | `git reset --hard`, `git clean -fdx`, `git push --force`, `git checkout -- .` |
| **Filesystem Write** | Any write to `/etc/`, `/usr/`, `/bin/`, `/boot/`, `/sys/`, `/proc/`, `/dev/` |
| **Self-Protect** | Agent cannot modify constraint system files (`hooks/`, `runtime/`) |
| **Bypass Vectors** | Detects base64, variable, alias, heredoc, eval, command substitution |

## Quick Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/kamanager2012/agent-constraint-system/main/install-remote.sh | bash

# Or via npm
npm install -g github:kamanager2012/agent-constraint-system

# Install for your agent
acs install          # Interactive menu
acs install --all    # All detected agents
```

Initialize after install:

```bash
# Claude Code
python3 ~/.claude/hooks/acs_lite.py init my-task "path/to/project"

# Codex CLI
python3 ~/.codex/hooks/acs_codex.py init

# CodeBuddy Code
python3 ~/.codebuddy/hooks/acs_lite.py init my-task "path/to/project"
```

## CLI

```bash
acs status           # Protection status
acs list             # Supported agents
acs version          # Version info
```

## Architecture

```
                    ACS Core (language-agnostic)
                ┌──────────────────────────────┐
                │  guard.py      Bash/Git patterns       │
                │  paths.py      Forbidden filesystem roots  │
                │  violations.py Sliding window + lock         │
                │  audit.py      JSONL audit logging       │
                │  structural.py Code structure validation │
                └──────────────┬───────────────┘
                               │
        ┌──────────┬───────────┼───────────┬──────────┐
        ▼          ▼           ▼           ▼          ▼
    Codex CLI  Claude Code  Gemini CLI  Cursor    CodeBuddy
     (CACS)      (ACS)       (GACS)     (CrACS)    (BACS)
```

## Safety Design

- **Sliding Window Lock** — Violations accumulate; lock triggers at threshold (80/150)
- **Integrity Chain** — SHA-256 hash chain detects tampering with constraint files
- **Self-Protection** — Agent cannot modify or disable its own safety layer
- **Human Authorization** — Unlock requires `--confirm` flag (agent cannot self-unlock)
- **Zero Dependencies** — ACS core has no external dependencies beyond Python stdlib

## Benchmark

ACS ships with a 105-scenario safety benchmark covering:

| Category | Scenarios |
|----------|-----------|
| Dangerous Bash | 30 |
| Git Destructive | 15 |
| Filesystem Write | 20 |
| Bypass Attempts | 20 |
| Self-Protect | 10 |
| False Positive | 10 |

```bash
cd benchmarks && python3 runner.py
```

See [benchmarks/RESULTS.md](benchmarks/RESULTS.md) for full results.

## Documentation

- [Codex Integration Guide](docs/codex-integration.md) — Setup, configuration, troubleshooting
- [Benchmark Results](benchmarks/RESULTS.md) — Detailed scenario-by-scenario results
- [中文文档](README.zh-CN.md)

## License

MIT — see [LICENSE](LICENSE) for details.
