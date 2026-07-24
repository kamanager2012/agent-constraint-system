# Changelog

> **Versioning note:** Prior development builds used inconsistent internal version numbers.
> Versioning was normalized to SemVer starting with v1.5.0. See [docs/version-history.md](docs/version-history.md)
> for the full mapping table.

## v1.6.0 (2026-07-25)

### Fixed — Self-Protection filesystem-level hardening (Task #5)

The ACS self-protect layer had two structural gaps that let a guarded agent
tamper with its own guard at runtime:

1. **Write path was never checked against agent runtime/hooks dirs.**
   Adapters' `handle_write` only tested `is_forbidden_path` (system roots), and
   the shared `filesystem_guard.py` actually *whitelisted* `.claude/hooks/` and
   `.claude/runtime/` via `WRITABLE_PREFIXES`. An agent could overwrite engine
   files (`acs_lite.py`), clear `VIOLATIONS.json`, or move hook scripts aside.
   - Added `is_self_protect_path()` to `paths.py`, covering **all 9 supported
     agents** (`.claude` `.codebuddy` `.codex` `.cursor` `.gemini` `.grok`
     `.hermes` `.opencode` `.qoder-cn`) plus the shared `.acs_core` core
     (hooks / runtime / governance / `*_runtime` subdirs).
   - Benchmark `run_write_scenario` now exercises `is_self_protect_path` — the
     same guard the runtime uses — so the `self_protect` category is faithfully
     tested (was 20%, now 100%).
   - `filesystem_guard.py` (the live Write/Bash gate for all orchestrator agents)
     now blocks self-protect paths *before* the writable whitelist, in both
     `_check_write` and `_check_bash`.

2. **Bash self-protect patterns were bypassable / incomplete.**
   - `rm\s+\S*\.claude/...` could not cross the space in `rm -rf /path` → fixed
     with `.*?` matching.
   - Missing patterns for `mv`/`cp`/`truncate`/`shred`, generic `>`/`>>`
     redirection, `sed -i`, and `ln -s` into agent dirs → added across all 9
     agents.
   - Command-splitting (P0-1) shredded fork bombs and alias-def-then-exec
     (`;`, `&`, `|` inside the command). Added `_WHOLE_CMD_PATTERNS` checked
     against the un-split command → `bash-011` and `bypass-008` now block.

### Changed — Benchmark expectation corrections (not gaming)
- `bash-020` (`rm -rf /tmp/...`): corrected to `allow` with a note. `/tmp` is an
  intentional policy exception (removed from `FORBIDDEN_ROOTS` in v1.5.0) so
  agents may manage temp recovery data; tracked as a known accepted risk.
- `bypass-010` / `bypass-011`: corrected to `block`. `xargs ... rm -rf` and
  `find -exec rm` are genuinely destructive and the guard (correctly) blocks
  them fail-closed; prior `allow` expectations + "missing pattern" notes were
  mislabeled.

### Result
- Full benchmark: **105/105 (100%)**, all 6 categories 100%.
  (Bypass-resistance 75.1% is informational — bypass *variants* evade detection;
  they are not counted in pass/fail.)
- Live `filesystem_guard.py` verified to block sp-001…sp-010 while allowing
  benign writes/commands.

> Known limitations (pre-existing, out of scope for Task #5): Levels 2/3 show
> 1 policy mismatch each in `asset_ledger` (expects CONFIRM, returns BLOCK on
> critical assets with no backup). These are asset-ledger decisions, not
> self-protect regressions.

## v1.5.0 (2026-07-22)

### Added
- Asset Ledger: asset provenance tracking with lifecycle states
- Tri-state Gate: ALLOW / CONFIRM / BLOCK decisions
- Safe Mode: post-error protection (2+ errors → CONFIRM)
- Levels 2 & 3 Benchmarks: 6 asset-aware + 6 trajectory scenarios
- Asset Ledger + SafeMode integration into acs_lite.py and acs_codex.py

### Fixed
- install-remote.sh, package.json: GitHub URL (jamesoldman→kamanager2012)
- install.sh: broken install_hermes() function
- guard.py: mv/cp/ln system injection, --force-with-lease FP, --staged FP
- guard.py: base64/xxd/openssl/nc pipe detection, nested subshell detection
- benchmark stats: README/RESULTS/runner now consistent (FP=0%)
- Bypass resistance: 8.7% → 50.1%

### Changed
- Version unified to single-source-of-truth via `VERSION` file
- Adapters no longer carry independent version numbers
- Historical version snapshots moved out of active package path
- README: English rewrite with benchmark data
- docs: removed over-promising claims
- application: repositioned as complement to Codex
- FORBIDDEN_ROOTS: removed /tmp
