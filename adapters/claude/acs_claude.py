#!/usr/bin/env python3
"""
acs_claude.py -- Claude Code Adapter

Imports from acs_core. Claude is just another adapter, not the canonical source.
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path

CORE_DIR = os.path.join(Path.home(), ".acs_core")
sys.path.insert(0, CORE_DIR)

from guard import check_bash_with_context
from paths import is_forbidden_path
from violations import add_violation, clear_violations, window_score, should_lock, load_violations, integrity_store, integrity_verify
from audit import AuditLogger
from asset_ledger import AssetLedger
from safe_mode import SafeMode

CLAUDE_DIR = Path.home() / ".claude"
RUNTIME_DIR = CLAUDE_DIR / "runtime"
VIOLATIONS_FILE = RUNTIME_DIR / "VIOLATIONS.json"
LOCK_FILE = RUNTIME_DIR / "LOCKED"
INTEGRITY_FILE = RUNTIME_DIR / "INTEGRITY.json"
AUDIT_LOG = RUNTIME_DIR / "tool-audit.jsonl"

audit = AuditLogger(AUDIT_LOG)
ledger = AssetLedger(str(RUNTIME_DIR / "asset_ledger.json"))
safe_mode = SafeMode()


def _deny(reason):
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": f"[ACS] {reason}"}}, sys.stdout)
    sys.exit(0)


def handle_bash(data):
    cmd = data.get("tool_input", {}).get("command", "").strip()
    if not cmd:
        return
    if "acs_claude.py unlock" in cmd:
        return
    result = check_bash_with_context(cmd, asset_ledger=ledger, error_count=safe_mode.error_count())
    if result["decision"] == "BLOCK":
        audit.log("PreToolUse", "Bash", data.get("session_id", ""), "deny", result["reason"])
        _deny(result["reason"])
    elif result["decision"] == "CONFIRM":
        audit.log("PreToolUse", "Bash", data.get("session_id", ""), "confirm", result["reason"])
        _deny(f"[CONFIRM] {result['reason']}")
    if should_lock(load_violations(VIOLATIONS_FILE)):
        _deny(f"System locked (window={window_score(load_violations(VIOLATIONS_FILE))})")


def handle_write(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return
    root = is_forbidden_path(fp)
    if root:
        ws, locked, _ = add_violation(VIOLATIONS_FILE, LOCK_FILE, f"forbidden:{fp}", 100)
        _deny(f"Write to {fp} (under {root}) forbidden")


def cli():
    cmd = sys.argv[1]
    if cmd == "init":
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        integrity_store(INTEGRITY_FILE, [Path(__file__).resolve()])
        print("[ACS Claude] Initialized with Asset Ledger + Safe Mode")
        sys.exit(0)
    elif cmd == "unlock":
        clear_violations(VIOLATIONS_FILE, LOCK_FILE)
        safe_mode.reset()
        audit.clear()
        print("[ACS Claude] Unlocked")
        sys.exit(0)
    elif cmd == "status":
        v = load_violations(VIOLATIONS_FILE)
        ws, locked = window_score(v), should_lock(v)
        ok, msg = integrity_verify(INTEGRITY_FILE)
        print(f"[ACS Claude] ws={ws} locked={locked} integrity={msg} assets={len(ledger._assets)} safe={safe_mode.is_active()}")
        sys.exit(0)


def main():
    if len(sys.argv) > 1:
        cli()
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    event, tool = data.get("hook_event_name", ""), data.get("tool_name", "")
    if event == "PreToolUse":
        if tool == "Bash": handle_bash(data)
        elif tool in ("Write", "Edit"): handle_write(data)


if __name__ == "__main__":
    main()
