#!/usr/bin/env python3
"""
acs_codex.py — CACS v2.0 Codex CLI Adapter

Production-grade constraint layer for Codex CLI.
Imports all guard logic from acs_core/ — this file is just the 
Codex-specific hook format adapter (~100 lines of glue).

Hook events: PreToolUse (Bash/Write), PostToolUse (audit), 
             SessionStart (init), Stop (session end)

CLI: acs_codex.py init | status | unlock --confirm | reset --force --confirm
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Find and import shared core
CORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".acs_core")
if not os.path.isdir(CORE_DIR):
    CORE_DIR = os.path.join(Path.home(), ".acs_core")
sys.path.insert(0, CORE_DIR)

from acs_core import (
    check_bash,
    FORBIDDEN_ROOTS,
    is_forbidden_path,
    add_violation,
    clear_violations,
    should_lock,
    window_score,
    load_violations,
    integrity_store,
    integrity_verify,
    AuditLogger,
)

# ── Agent-specific paths ─────────────────────────────────────────────────────
CODEX_DIR = Path.home() / ".codex"
HOOKS_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = CODEX_DIR / "cacs_runtime"
VIOLATIONS_FILE = RUNTIME_DIR / "violations.json"
LOCK_FILE = RUNTIME_DIR / "LOCK.json"
INTEGRITY_FILE = RUNTIME_DIR / "integrity.json"
AUDIT_LOG = RUNTIME_DIR / "tool-audit.jsonl"
CRITICAL_FILES = [Path(__file__).resolve()]

audit = AuditLogger(AUDIT_LOG)


# ── Helper ───────────────────────────────────────────────────────────────────

def _deny(reason: str) -> None:
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[CACS] {reason}",
        }
    }, sys.stdout)
    sys.exit(0)


# ── Event Handlers ───────────────────────────────────────────────────────────

def handle_bash(data: dict) -> None:
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    cmd = command.strip()
    # Always allow unlock/reset (whitelist)
    if "acs_codex.py unlock" in cmd or ("acs_codex.py reset" in cmd and "--force" in cmd):
        return

    # Check dangerous patterns
    result = check_bash(command)
    if result:
        audit.log("PreToolUse", "Bash", data.get("session_id", ""), "deny", result)
        _deny(result)

    # Violation check: if locked, deny
    if should_lock(load_violations(VIOLATIONS_FILE)):
        ws = window_score(load_violations(VIOLATIONS_FILE))
        _deny(f"System locked (violation window={ws})")


def handle_write(data: dict) -> None:
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return

    # Forbidden root check
    root = is_forbidden_path(fp)
    if root:
        ws, locked, _ = add_violation(VIOLATIONS_FILE, LOCK_FILE, f"forbidden: {fp}", 100)
        audit.log("PreToolUse", data.get("tool_name", ""), data.get("session_id", ""),
                  "deny", f"forbidden_root: {root}")
        _deny(f"Write to {fp} (under {root}) is forbidden")

    # Self-protection
    if str(HOOKS_DIR) in str(Path(fp).resolve()):
        ws, locked, _ = add_violation(VIOLATIONS_FILE, LOCK_FILE, f"self_protect: {fp}", 100)
        _deny("Cannot modify CACS system files")


def handle_session_start(data: dict) -> None:
    if RUNTIME_DIR.exists():
        audit.log("SessionStart", "", data.get("session_id", ""), "init")


# ── CLI ──────────────────────────────────────────────────────────────────────

def cli() -> None:
    cmd = sys.argv[1]
    if cmd == "init":
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        integrity_store(INTEGRITY_FILE, CRITICAL_FILES)
        ok, msg = integrity_verify(INTEGRITY_FILE)
        print(f"[CACS] Initialized: {RUNTIME_DIR}")
        print(f"[CACS] Integrity: {msg}")
        sys.exit(0)

    elif cmd == "unlock":
        if "--confirm" not in sys.argv:
            print("[CACS] unlock requires explicit human authorization.", file=sys.stderr)
            print("[CACS] Run: acs_codex.py unlock --confirm", file=sys.stderr)
            sys.exit(1)
        clear_violations(VIOLATIONS_FILE, LOCK_FILE)
        audit.clear()
        print("[CACS] Unlocked. Violations and audit cleared.")
        sys.exit(0)

    elif cmd == "reset":
        if "--confirm" not in sys.argv:
            print("[CACS] reset requires explicit human authorization.", file=sys.stderr)
            print("[CACS] Run: acs_codex.py reset --force --confirm", file=sys.stderr)
            sys.exit(1)
        if "--force" in sys.argv:
            for f in RUNTIME_DIR.glob("*"):
                f.unlink()
            print("[CACS] Full reset — all runtime state cleared.")
        else:
            print("[CACS] Use --force to confirm full reset.")
        sys.exit(0)

    elif cmd == "status":
        print("[CACS v2.0] Status Report")
        if not RUNTIME_DIR.exists():
            print("  Status: NOT INITIALIZED (run init first)")
            sys.exit(0)
        v = load_violations(VIOLATIONS_FILE)
        ws = window_score(v)
        locked = should_lock(v)
        ok, msg = integrity_verify(INTEGRITY_FILE)
        print(f"  Violations: window_score={ws}, locked={locked}")
        print(f"  Audit: {audit.total_count()} entries, {audit.denied_count()} denied")
        print(f"  Integrity: {msg}")
        sys.exit(0)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) > 1:
        cli()

    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")

    if event == "PreToolUse":
        if tool == "Bash":
            handle_bash(data)
        elif tool in ("Write", "Edit", "MultiEdit", "apply_patch"):
            handle_write(data)
    elif event == "PostToolUse":
        audit.log(event, tool, data.get("session_id", ""), "allow")
        resp = data.get("tool_response", "")
        if isinstance(resp, str) and resp:
            audit.log(event, tool, data.get("session_id", ""), "allow",
                      f"response_size: {len(resp)}")
    elif event == "SessionStart":
        handle_session_start(data)
    elif event == "Stop":
        audit.log(event, tool, data.get("session_id", ""), "stop")


if __name__ == "__main__":
    main()
