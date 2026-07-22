# ACS 版本历史

## v5.3 (2026-07-13) — 当前

### scope 文件统一 (P1)

- `_load_scope()` 改为读取 `ACTIVE_TASK.json` 权威源，`TASK_SCOPE.json` 仅作兼容回退
- 消除双文件同步漂移风险：`check_write`/`check_bash` 现在与 `_active_task_read` 读取同一文件

## v5.2 (2026-07-13)

### 配置文件保护扩展 (P0)

- `ACS_SYSTEM_FILES` 新增 `settings.json`, `settings.local.json`, `CLAUDE.md`, `.claude.json`
- `_is_acs_system_path` 新增 4 个配置文件精确匹配（防御纵深）
- 关闭 Bash 写入绕过 ZONE 检查的缺口

## v5.1 (2026-07-13)

### runtime/ 目录完整保护 (P0)

- **攻击向量**: `_is_acs_system_path` 仅保护 3 路径，agent 可 Write/Edit `ACTIVE_TASK.json` 改 `allowed_dirs` 禁用 ACS
- **修复**: `_is_acs_system_path` + `ACS_SYSTEM_FILES` 扩展至完整 `runtime/` 目录
- 删除 token-optimizer 插件（硬编码 150K 上下文压缩阈值）

## v5.0 (2026-06-06)

### 统一优化

- acs_lite.py v5.0 重构：单文件合并模块，减少调用开销
- hook_orchestrator.py v5.0：统一调度，PreToolUse/PostToolUse/Stop 三阶段
- ACS_SELF_PROTECT：hooks/ 目录不可变保护，任何 scope 外写入秒锁(100分)
- unlock 白名单：锁死状态也可执行，防死锁
- integrity-store：手动操作后重建基线，防 TAMPERED 误报

### 2026-06-09 审计修复

- **死锁修复**: bash_guard.py 缩进错误导致 Python 崩溃 → 所有 Bash 被拦截，含 unlock
  - 根因: GLM 写入有缩进的 docstring (`  """`)
  - 修复: 去缩进
  - 防护: ACS_GUIDE.md 增加"死锁解封步骤"
- **GLM 篡改清理**: 中文副本文件、Zone.Identifier、.bak 残留全部删除
- **嵌套目录清理**: `.claude/hooks/.claude/` (15MB) 删除
- **双轨消除**: settings.json 与 settings.local.json hook 注册重复 → 仅保留 settings.json
- **配置同步**: orchestrator_config.json 与 settings.json hooks 完全对齐
- **文档重建**: ACS_GUIDE.md v5.0 操作指南（解锁、scope、死锁解封、常见错误）

### 已知陷阱

1. `init` 修改 ACTIVE_TASK.json → 触发 ACS_SELF (100) → 必须紧接 unlock+reset+integrity-store
2. `echo reset VIOLATIONS` → integrity TAMPERED → 必须紧接 integrity-store
3. `rm -rf` 触发 DANGEROUS_BASH → 用 `mv` 替代
4. settings.local.json hook 变更 → 需重启会话或打开 /hooks 才生效
5. hook 语法错误能造成全 Bash 死锁 → 只有终端手动操作能解封

## v4.2 (2026-06-05)

### 控制流重构 (P0)

- **P0-1**: proposal_guard 从 PreToolUse 移至 PostToolUse（控制流语义对齐）
- **P0-1b**: acs_lite 加 `_infer_from_path` fallback（防止双门→无门）
- **P0-2**: `clear_violations` 真重置（events=[] + genesis baseline，不再只追加负分）
- **P0-3**: 白名单从 closed-world 改为 open-world + `is_relative_to` 防遍历
- Safety asserts: path escape / scope / chain 3 行一致性检查

### P1 修复

- **P1-4**: audit/ 从 PROTECTED 移至 RUNTIME zone（append-only，可写不可删）

### P2 修复

- **P2-6**: rm -rf 正则收窄（只拦截 //~/--* 目标，空目录不再误触发）
- **P2-7**: read_guard 对 settings.json 研发模式允许读取+警告

### 根因诊断

ACS 核心问题不是「规则不够多」而是「控制流语义错位」：
- PreToolUse 做了 PostToolUse 的事
- state reset 没有 reset chain
- whitelist 是 closed-world 而不是 open-world

## v4.1 (2026-06-03)

- 模块化拆分：acs_lite / acs_paths / acs_violations / acs_structural
- 滑动窗口锁：window_score ≥ 80 自动锁
- ZONE 分区权限：WORKSPACE / SOURCE / RUNTIME / SYSTEM
- 完整性链：17 个 CRITICAL_FILES sha256 滚动哈希
- Shadow Workspace：create → diff → merge 原子合入
- hook_orchestrator 统一调度

## v4.0 (2026-05-30)

- C-1 自死锁修复：SCOPE_BASELINE 白名单
- C-2 secret 泄露：SENSITIVE_PATH_PATTERNS
- C-3 PROPOSAL 路径统一到 audit/proposals.jsonl
- C-4 11 个孤儿 .py 集成
- 滑动窗口替换固定阈值衰减
- 完整性链 v4.0：自指修复

## v1.0.0 (2026-05-30)

- TypeScript 原型 → 单体 acs_lite.py
- 基础 PreToolUse 拦截
- 硬编码 PROJECT 路径

## v0.7.1 (2026-05-29)

- ACS v0.7.1 边界验证
- PreToolUse hook 注册

## v0.7.0 (2026-05-28)

- ACS 原型：PreToolUse hook 基础框架
- 路径保护与白名单机制
