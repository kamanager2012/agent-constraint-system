# acs_core/paths.py — Agent-agnostic path protection
# Used by all ACS adapter variants.

import os
from pathlib import Path
from typing import Set

# ── Forbidden system roots ──────────────────────────────────────────────────

FORBIDDEN_ROOTS: Set[str] = {
    "/", "/bin", "/boot", "/dev", "/etc", "/lib", "/lib64",
    "/proc", "/root", "/run", "/sbin", "/sys", "/usr", "/var",
}


def is_forbidden_path(fp: str) -> str | None:
    """Check if a file path is under a forbidden system root.
    Returns the matching root if forbidden, None if allowed.
    """
    resolved = str(Path(fp).resolve())
    for root in FORBIDDEN_ROOTS:
        if resolved == root or resolved.startswith(root + os.sep):
            return root
    return None


def is_self_protect(fp: str, protected_dirs: list[str]) -> bool:
    """Check if a file path is within protected directories (self-protection)."""
    resolved = str(Path(fp).resolve())
    return any(d in resolved for d in protected_dirs)
