#!/usr/bin/env python3
"""
qacs.py — QACS v2.0 Qoder CN CLI Adapter

Qoder's hook system is nearly identical to Codex CLI. Same JSON stdin format,
same exit codes (0=allow, 2=block). Paths: ~/.qoder-cn/ instead of ~/.codex/.

CLI: qacs.py init | status | unlock --confirm | reset --force --confirm
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path

sys.path.insert(0, os.path.join(Path.home(), ".acs_core"))

from acs_core import (  # type: ignore
    check_bash, FORBIDDEN_ROOTS, is_forbidden_path,
    add_violation, clear_violations, should_lock, window_score, load_violations,
    integrity_store, integrity_verify, AuditLogger,
)

QODER_DIR = Path.home() / ".qoder-cn"
HOOKS_DIR = QODER_DIR / "hooks"
RUNTIME_DIR = QODER_DIR / "qacs_runtime"
VIOLATIONS_FILE = RUNTIME_DIR / "violations.json"
LOCK_FILE = RUNTIME_DIR / "LOCK.json"
INTEGRITY_FILE = RUNTIME_DIR / "integrity.json"
AUDIT_LOG = RUNTIME_DIR / "tool-audit.jsonl"

audit = AuditLogger(AUDIT_LOG)


def deny(reason: str) -> None:
    sys.stderr.write(f"[QACS] {reason}\n")
    sys.exit(2)  # Qoder uses exit code 2 for block


def handle_pretool(data: dict) -> None:
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {})
    sid = data.get("session_id", "")

    if tool == "Bash":
        cmd = inp.get("command", "")
        if not cmd:
            return
        if "qacs.py unlock" in cmd or ("qacs.py reset" in cmd and "--force" in cmd):
            return
        result = check_bash(cmd)
        if result:
            audit.log("PreToolUse", tool, sid, "deny", result)
            deny(result)
        if should_lock(load_violations(VIOLATIONS_FILE)):
            deny(f"System locked (window={window_score(load_violations(VIOLATIONS_FILE))})")

    elif tool in ("Write", "Edit", "MultiEdit"):
        fp = inp.get("file_path", "")
        if fp:
            root = is_forbidden_path(fp)
            if root:
                add_violation(VIOLATIONS_FILE, LOCK_FILE, f"forbidden: {fp}", 100)
                deny(f"Write to {fp} (under {root}) is forbidden")
            if str(HOOKS_DIR) in str(Path(fp).resolve()):
                add_violation(VIOLATIONS_FILE, LOCK_FILE, f"self_protect: {fp}", 100)
                deny("Cannot modify QACS system files")


def cli() -> None:
    cmd = sys.argv[1]
    if cmd == "init":
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        integrity_store(INTEGRITY_FILE, [Path(__file__).resolve()])
        ok, msg = integrity_verify(INTEGRITY_FILE)
        print(f"[QACS] Initialized: {RUNTIME_DIR}")
        print(f"[QACS] Integrity: {msg}")
        sys.exit(0)
    elif cmd == "unlock":
        if "--confirm" not in sys.argv:
            print("[QACS] unlock requires --confirm", file=sys.stderr); sys.exit(1)
        clear_violations(VIOLATIONS_FILE, LOCK_FILE); audit.clear()
        print("[QACS] Unlocked."); sys.exit(0)
    elif cmd == "reset":
        if "--confirm" not in sys.argv:
            print("[QACS] reset requires --confirm", file=sys.stderr); sys.exit(1)
        if "--force" in sys.argv:
            for f in RUNTIME_DIR.glob("*"): f.unlink()
            print("[QACS] Full reset."); sys.exit(0)
        print("[QACS] Use --force."); sys.exit(0)
    elif cmd == "status":
        print("[QACS v2.0] Status Report")
        if not RUNTIME_DIR.exists():
            print("  NOT INITIALIZED (run init)"); sys.exit(0)
        v = load_violations(VIOLATIONS_FILE)
        ok, msg = integrity_verify(INTEGRITY_FILE)
        print(f"  Violations: window={window_score(v)}, locked={should_lock(v)}")
        print(f"  Audit: {audit.total_count()} entries, {audit.denied_count()} denied")
        print(f"  Integrity: {msg}"); sys.exit(0)


def main() -> None:
    if len(sys.argv) > 1:
        cli()
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    event = data.get("hook_event_name", "")
    if event == "PreToolUse":
        handle_pretool(data)
    elif event == "PostToolUse":
        audit.log(event, data.get("tool_name", ""), data.get("session_id", ""), "allow")
    elif event == "SessionStart":
        if RUNTIME_DIR.exists():
            audit.log(event, "", data.get("session_id", ""), "init")
    elif event == "Stop":
        audit.log(event, "", data.get("session_id", ""), "stop")


if __name__ == "__main__":
    main()
