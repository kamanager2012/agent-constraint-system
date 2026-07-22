# Agent Constraint System (ACS)

> Production-grade safety layer for AI coding agents. 8 agents, 1 core, 1 command.

## Install

| Method | Command |
|--------|---------|
| **npm** | `npm install -g github:kamanager2012/agent-constraint-system` |
| **curl** | `curl -fsSL https://raw.githubusercontent.com/jamesoldman/agent-constraint-system/main/install-remote.sh \| bash` |
| **GitHub** | `git clone https://github.com/jamesoldman/agent-constraint-system.git && cd agent-constraint-system && ./install.sh` |

After install:

```bash
acs install          # auto-detect + select agents
acs status           # check protection status

The installer auto-detects installed agents and shows a selection menu. Specific agents can be installed directly:

```bash
acs install claude codex     # specific agents
acs install --all            # everything detected
acs status                   # check what's installed
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
