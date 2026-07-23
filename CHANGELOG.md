# Changelog

> **版本命名规则:** 功能大改进才能用 `.1`（minor），否则只能用 `.0.1`（patch）。
> v1.5.0 之前的版本号为历史遗留，曾存在 v0.7→v1.0→v1.1.0→v1.2.0→v5.3→v6.x 的虚高跳跃，
> 2026-07-23 统一修正为语义化版本：v1.0.0→v1.1.0→v1.2.0→v1.3.0→v1.4.0→v1.5.0。

## v1.5.0 (2026-07-22)

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
- **Version unified**: corrected from v6.1.0→v5.3.0→v1.5.0 per semantic versioning rules

---

## 历史版本映射

| 当前版本 | 历史虚高版本 | 日期 | 主要变更 |
|----------|-------------|------|----------|
| v1.5.0 | v5.3.0 / v6.1.0 | 2026-07-22 | Asset Ledger + Safe Mode + 3-level benchmark |
| v1.4.0 | v5.0 | 2026-06-06 | 策略引擎、多 Agent 治理、hook_orchestrator |
| v1.3.0 | v4.3 | (planned) | 独立安装、环境变量、相对路径 |
| v1.2.0 | v1.2.0 | 2026-06-05 | 控制流重构、clear_violations 修复、审计区修复 |
| v1.1.0 | v1.1.0 | 2026-06-03 | Python 纯化重写、滑动窗口锁、zone 分区 |
| v1.0.0 | v1.0.0 | 2026-05-30 | 自保护正则、SHA256 完整性链、项目解耦 |
| v0.2.0 | v0.7.1 | 2026-05-30 | 7 个 CRITICAL + 6 个 HIGH 修复、114 测试 |
| v0.1.0 | v0.7.0 | 2026-05-29 | TypeScript+Python 混合原型、首次审计 |
