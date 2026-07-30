# Agent Constraint System (ACS)

> A cross-agent runtime safety layer for autonomous coding agents.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green.svg)](https://python.org)

## At a Glance

ACS prevents coding agents from executing dangerous commands, modifying protected files, or circumventing safety constraints — using both pattern matching (Level 1) and asset-aware context (Level 2).

| Suite | Scenarios | Pass Rate |
|-------|-----------|-----------|
| Level 1 (Pattern) | 105 | 94.3% (99/105) |
| Level 2 (Asset) | 6 | 100% (6/6) |
| Level 3 (Trajectory) | 7 | 100% (7/7) |
| Level 4 (Capability) | 5 | 100% (5/5) |

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

ACS ships with a 123-scenario safety benchmark across four levels:

| Level | Focus | Scenarios | Runner |
|-------|-------|-----------|--------|
| Level 1 | Pattern matching | 105 | `benchmarks/runner.py` |
| Level 2 | Asset-aware (Asset Ledger) | 6 | `benchmarks/level2/runner.py` |
| Level 3 | Trajectory safety | 7 | `benchmarks/level3/runner.py` |
| Level 4 | Capability preservation (Capability Ledger) | 5 | `benchmarks/level4/runner.py` |

```bash
cd benchmarks && python3 runner.py           # Level 1
cd benchmarks/level2 && python3 runner.py    # Level 2
cd benchmarks/level3 && python3 runner.py    # Level 3
cd benchmarks/level4 && python3 runner.py    # Level 4
```

See [benchmarks/RESULTS.md](benchmarks/RESULTS.md) for Level 1 full results.

### Known Gaps (honest, v1.7.1+ roadmap)

The benchmark is an independent contract — `expected` labels never follow the
implementation. Of 105 Level 1 scenarios, 6 honestly fail:

- **4 known command-obfuscation bypasses** — string-concat, sed, octal-escape, DNS-exfil pipes evade static regex
- **2 legitimate cleanup commands blocked** — `rm -rf ./node_modules` / `rm -rf ./dist ./build ./.cache` caught by the Level 1 pattern-layer blanket (the asset-aware runtime path already allows these)

| Gap | Scenarios | Cause | Roadmap |
|-----|-----------|-------|---------|
| Static-detection bypasses | bypass-007, bypass-016, bypass-017, bypass-020 | String-concat, sed-obfuscation, octal-escape, DNS-exfil pipes evade regex | Layer 2 trajectory analysis |
| Pattern-layer false positives | fp-001, fp-002 | Level 1 blanket `rm -rf` block catches legit cleanup (runtime asset-aware path allows it) | Optional pattern-layer refinement |

A blanket block that disables legitimate agent work is reported here as a false
positive, not a safety win.

## Documentation

- [Codex Integration Guide](docs/codex-integration.md) — Setup, configuration, troubleshooting
- [Benchmark Results](benchmarks/RESULTS.md) — Detailed scenario-by-scenario results
- [中文文档](README.zh-CN.md)

## License

MIT — see [LICENSE](LICENSE) for details.
