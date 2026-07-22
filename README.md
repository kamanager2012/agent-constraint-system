# Agent Constraint System (ACS)

> A safety layer for AI coding agents. It sits between the agent and your system, blocking dangerous operations before they execute.

**8 agents registered, 6 ready to deploy, 1 shared core, 1 installer.**

## Quick Install

```bash
git clone https://github.com/jamesoldman/agent-constraint-system.git
cd agent-constraint-system
./install.sh
```

The installer auto-detects which agents you have installed and lets you pick:

```
  Select agents to protect:

  1) 🎯 Claude Code            detected
  2) 🔷 Codex CLI (OpenAI)     detected
  3) ✨ Gemini CLI (Google)     detected
  4) ⬛ Cursor                  detected
  5) 📦 OpenCode                detected

  a) All detected
  q) Quit
```

Or install specific ones directly:

```bash
./install.sh claude codex        # Just those two
./install.sh --all               # Everything detected
./install.sh --verify            # Check status
```

## What It Blocks

| Category | Examples |
|----------|----------|
| Dangerous Bash | `rm -rf /`, `kill -9`, `mkfs`, `dd if=/dev/`, `chmod 777 /etc`, curl-pipe-shell |
| Destructive Git | `git reset --hard`, `git restore --worktree -- .`, `git push --force`, `git clean -fdx` |
| System writes | Any write to `/etc/`, `/usr/`, `/bin/`, `/boot/`, `/sys/`, and 10 other forbidden roots |
| Self-modification | Agent cannot modify the constraint system's own files |

## CLI Commands

| Command | Purpose |
|---------|---------|
| `init` | Create runtime directory (required first step) |
| `status` | Show violations, audit entries, integrity |
| `unlock --confirm` | Clear violations and unlock (requires human flag) |
| `reset --force --confirm` | Full state reset (requires human flags) |

## Architecture

```
┌─────────────────────────────────────────────┐
│  acs_core/         Shared Logic              │
│  guard.py          Bash + Git patterns       │
│  paths.py          Forbidden root detection  │
│  violations.py     Sliding window + lock     │
│  audit.py          JSONL audit logging       │
│  structural.py     Code structure validation │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
 ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
 │Claude│ │Codex │ │Cursor│ │Gemini│ │Open  │
 │ Code │ │ CLI  │ │      │ │ CLI  │ │Code  │
 │ ACS  │ │CACS  │ │CrACS │ │GACS  │ │OACS  │
 └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
  Python    Python   Shell    Python   TypeScript
```

## Security Design

- **No auto-initialization** — runtime directory must be explicitly created via `init`
- **Unlock requires `--confirm`** — prevents the agent from autonomously bypassing restrictions
- **Sliding window** — violations accumulate; crossing threshold triggers lock
- **Integrity chain** — SHA-256 hash chain detects tampering with constraint system files
- **Self-protection** — agent cannot modify its own guards

## License

MIT — see `LICENSE`.
