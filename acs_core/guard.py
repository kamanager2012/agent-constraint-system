# acs_core/guard.py — Agent-agnostic Bash and Git guard patterns
# Used by all ACS adapter variants.

import re
from typing import List, Tuple

# ── Dangerous Bash patterns ──────────────────────────────────────────────────

DANGEROUS_BASH: List[Tuple[str, str]] = [
    # rm -rf /, rm -rf /*, rm -rf ~, rm -rf *
    (r'(?:^|[|;]\s*)rm\s+(?:-[a-z]*f[a-z]*\s+)+(?:/$(?:\s|$)|/\*\s|~(?:\s|$)|\*(?:\s|$))',
     "rm -rf targeting root/home/wildcard"),
    (r'(?:^|[|;]\s*)kill\s+-9\b', "kill -9 (force kill)"),
    (r'(?:^|[|;]\s*)mkfs\.', "mkfs (disk format)"),
    (r'(?:^|[|;]\s*)dd\s+if=/dev/', "dd writing to block device"),
    # chmod 777 on system paths
    (r'chmod\s+(?:-R\s+)?777\s+/(?:etc|usr|bin|sbin|var|tmp|home|root|opt)/',
     "chmod 777 on system path"),
    # fork bomb
    (r':\(\)\s*\{', "fork bomb pattern"),
    # overwrite critical files
    (r'>\s*/(?:etc|boot)/', "redirect overwrite to system path"),
    (r'curl.*\|.*(?:ba)?sh', "curl-pipe-shell (unverified source)"),
]

COMPILED_DANGEROUS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in DANGEROUS_BASH]

# ── Git destructive patterns ────────────────────────────────────────────────

GIT_DESTRUCTIVE: List[Tuple[str, str]] = [
    (r'git\s+restore\s+.*--\s+\.$', "git restore -- . (uncontrolled overwrite)"),
    (r'git\s+reset\s+--hard', "git reset --hard (destroys uncommitted work)"),
    (r'git\s+clean\s+-[fdx]+', "git clean (deletes untracked files)"),
    (r'git\s+push\s+--force', "git push --force (overwrites remote history)"),
    (r'git\s+push\s+-f\b', "git push -f (overwrites remote history)"),
    (r'git\s+checkout\s+--\s+\.', "git checkout -- . (discards all changes)"),
]

COMPILED_GIT = [(re.compile(p, re.IGNORECASE), desc) for p, desc in GIT_DESTRUCTIVE]


# ── Command cleaning ────────────────────────────────────────────────────────

def clean_command(cmd: str) -> str:
    """Remove content inside quotes and heredocs to prevent false matches."""
    result = cmd
    result = re.sub(r"'[^']*'", "''", result)
    result = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', result)
    result = re.sub(
        r'<<\s*["\']?(\w+)["\']?\s*\n.*?\n\s*\1',
        '<<HEREDOC>>', result, flags=re.DOTALL
    )
    return result


# ── Guard check ─────────────────────────────────────────────────────────────

def check_bash(command: str) -> str | None:
    """Check a Bash command against all dangerous patterns.
    Returns the blocking reason if dangerous, None if safe.
    """
    cleaned = clean_command(command)

    for pattern, desc in COMPILED_DANGEROUS:
        if pattern.search(cleaned):
            return f"Dangerous command blocked: {desc}"

    for pattern, desc in COMPILED_GIT:
        if pattern.search(command):
            return f"Destructive git blocked: {desc}"

    return None
