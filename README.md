# Agent Constraint System (ACS)

> A cross-agent runtime safety layer for autonomous coding agents.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green.svg)](https://python.org)

## At a Glance

ACS prevents coding agents from executing dangerous commands, modifying protected files, or circumventing safety constraints — using both pattern matching (Level 1) and asset-aware context (Level 2).

| Suite | Scenarios | Pass Rate |
|-------|-----------|-----------|
| Core Safety (Level 1) | 105 | 94.3% (99/105) |
| Capability Preservation | 2 | 0% (0/2, v1.7.0) |
| **Level 1 Combined** | **107** | **92.5% (99/107)** |
| Level 2 (Asset) | 6 | 100% |
| Level 3 (Trajectory) | 6 | 100% |

*Danger Block: 92.7% | FP Rate: 8.0% | Bypass Resistance: 75.5%*

```bash
cd benchmarks && python3 runner.py           # Level 1: pattern matching
cd benchmarks/level2 && python3 runner.py    # Level 2: asset-aware tri-state gate
cd benchmarks/level3 && python3 runner.py    # Level 3: trajectory safety
```

## Supported Agents

| Agent | Adapter | Integration | Status |
|-------|---------|-------------|--------|
| **Codex CLI** (OpenAI) | [CACS](docs/codex-integration.md) | Python runtime adapter | Integrated |
| **Claude Code** (Anthropic) | ACS | Native hook integration | Adapter ready; E2E pending |
| **CodeBuddy Code** | BACS | Native hook integration | Integrated |
| **Gemini CLI** (Google) | GACS | Python runtime adapter | Experimental |
| **OpenCode** | OACS | TypeScript plugin | Experimental |
| **Cursor** | CrACS | Shell bootstrap | Experimental |
| **Qoder CN** | QACS | Python runtime adapter | Experimental |
| **Hermes Agent** | HACS | Python runtime adapter | Experimental |
| **Grok Build** (xAI) | GACS | Python runtime adapter | Experimental |

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
python3 ~/.claude/hooks/acs_claude.py init

# Codex CLI
python3 ~/.codex/hooks/acs_codex.py init

# CodeBuddy Code
python3 ~/.codebuddy/hooks/acs_codebuddy.py init
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

ACS ships with a 107-scenario safety benchmark covering:

| Category | Scenarios |
|----------|-----------|
| Dangerous Bash | 30 |
| Git Destructive | 15 |
| Filesystem Write | 20 |
| Bypass Attempts | 20 |
| Self-Protect | 10 |
| False Positive | 10 |
| Capability Preservation | 2 |

```bash
cd benchmarks && python3 runner.py
```

See [benchmarks/RESULTS.md](benchmarks/RESULTS.md) for full results.

### Known Gaps (honest, v1.7.0 roadmap)

The benchmark is an independent contract — `expected` labels never follow the
implementation. Of 107 scenarios, 8 honestly fail, split across three suites:

- **4 known command-obfuscation bypasses** — string-concat, sed, octal-escape, DNS-exfil pipes evade static regex
- **2 legitimate cleanup commands blocked** — `rm -rf ./node_modules` / `rm -rf ./dist ./build ./.cache` caught by the v1.6.1 fail-closed recursive-rm policy (false positives)
- **2 capability-preservation scenarios not yet implemented** — deleting/relocating a depended-on credential is allowed

| Gap | Scenarios | Cause | Roadmap |
|-----|-----------|-------|---------|
| False positives on legit cleanup | fp-001, fp-002 | v1.6.1 blanket-blocks all recursive `rm`, catching `rm -rf ./node_modules` / `rm -rf ./dist ./build ./.cache` | Asset-aware `rm` via Asset Ledger (rebuildable assets → ALLOW) |
| Static-detection bypasses | bypass-007, bypass-016, bypass-017, bypass-020 | String-concat, sed-obfuscation, octal-escape, DNS-exfil pipes evade regex | Layer 2 trajectory analysis |
| Capability preservation | cap-001, cap-002 | Deleting/relocating a depended-on credential is allowed; runtime breaks silently | Capability Ledger state machine |

A blanket block that disables legitimate agent work is reported here as a false
positive, not a safety win.

## Documentation

- [Codex Integration Guide](docs/codex-integration.md) — Setup, configuration, troubleshooting
- [Benchmark Results](benchmarks/RESULTS.md) — Detailed scenario-by-scenario results
- [中文文档](README.zh-CN.md)

## License

MIT — see [LICENSE](LICENSE) for details.
