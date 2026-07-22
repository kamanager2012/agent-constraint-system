# Changelog

## v6.1.0 (2026-07-22)

### Added
- Asset Ledger: asset provenance tracking with lifecycle states
- Tri-state Gate: ALLOW / CONFIRM / BLOCK decisions
- Safe Mode: post-error protection (2+ errors → CONFIRM)
- Levels 2 & 3 Benchmarks: 6 asset-aware + 6 trajectory scenarios
- Asset Ledger + SafeMode integration into acs_lite.py and acs_codex.py v3.0

### Fixed
- install-remote.sh, package.json: GitHub URL (jamesoldman→kamanager2012)
- install.sh: broken install_hermes() function
- guard.py: mv/cp/ln system injection, --force-with-lease FP, --staged FP
- guard.py: base64/xxd/openssl/nc pipe detection, nested subshell detection
- benchmark stats: README/RESULTS/runner now consistent (FP=0%)
- Bypass resistance: 8.7% → 50.1%

### Changed
- README: English rewrite with benchmark data
- docs: removed over-promising claims
- application: repositioned as complement to Codex
- FORBIDDEN_ROOTS: removed /tmp

## v6.0.0 (2026-07-13)

### Added
- Initial release with 8 agent platforms
- Bash/Git/filesystem guard patterns
- Sliding window violations, SHA-256 integrity, JSONL audit
- npm install, interactive menu, CLI
- ACS v5.3 hooks with scope/mode/token budget
