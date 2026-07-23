# Changelog

> **Versioning note:** Prior development builds used inconsistent internal version numbers.
> Versioning was normalized to SemVer starting with v1.5.0. See [docs/version-history.md](docs/version-history.md)
> for the full mapping table.

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
