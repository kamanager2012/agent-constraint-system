# acs_core/guard.py — Agent-agnostic Bash and Git guard patterns
# Used by all ACS adapter variants.

import re
from typing import List, Tuple

# ── Dangerous Bash patterns ──────────────────────────────────────────────────

DANGEROUS_BASH: List[Tuple[str, str]] = [
    # DELETE — rm patterns
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+/(?:\s|$)",       "rm -rf /"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+\*",              "rm -rf *"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+~",                "rm -rf ~"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+\S*PROJ",         "rm -rf project"),
    # Intentionally omit generic rm pattern — scope-gated in acs_lite.py, not suitable
    # for shared core which lacks per-agent scope context
    (r"\btruncate\s+-s\s+0",                                   "truncate to zero"),

    # SYSTEM — dangerous system operations
    (r"(?:^|[|;&]\s*)kill\s+-9\b",                             "kill -9 (force kill)"),
    (r"(?:^|[|;&]\s*)mkfs\.",                                   "mkfs (disk format)"),
    (r"(?:^|[|;&]\s*)dd\s+if=/dev/",                           "dd writing to block device"),
    (r"\breboot\b",                                             "reboot"),
    (r"\bshutdown\b",                                           "shutdown"),
    (r":\(\s*\)\s*\{",                                         "fork bomb pattern"),

    # EXEC — inline interpreter (blocks python3 -c, perl -e, etc.)
    (r"\b(?:node|python3?|perl|ruby|php|lua)\s+-[ce]\b",      "inline interpreter execution"),
    (r"\b(?:python3?|node|perl|ruby|bash)\s+<<",               "heredoc interpreter"),
    (r"\beval\s+\$",                                            "eval with variable/substitution"),

    # BYPASS — encoding/decoding pipe chains
    (r"\bbase64\s+(?:-d|--decode).*\|.*(?:ba)?sh\b",         "base64 decode pipe to shell"),
    (r"\bxxd\s+-r\s+-p.*\|.*(?:ba)?sh\b",                    "xxd decode pipe to shell"),
    (r"\bopenssl\s+(?:base64|enc)\s+-d.*\|.*(?:ba)?sh\b",   "openssl decode pipe to shell"),
    (r"\b(?:nc|ncat)\s+.*\|\s*(?:ba)?sh\b",                   "netcat pipe to shell"),

    # WRITE — permission changes and file overwrites
    (r"\bchmod\s+777\b",                                       "chmod 777"),
    (r"\bchmod\s+(?:-R\s+)?777\s+/(?:etc|usr|bin|sbin|var|tmp|home|root|opt)/",
     "chmod 777 on system path"),
    (r"\bchown\s+root\b",                                      "chown root"),
    (r">\s*/etc/",                                              "overwrite /etc file"),
    (r">\s*/(?:etc|boot)/",                                     "redirect overwrite to system path"),

    # ANTI-FORENSIC — history manipulation
    (r"\bhistory\s+-[cw]\b",                                   "clear shell history"),
    (r"\bunset\s+HISTFILE\b",                                  "disable shell history"),
    (r"\bcat\s+/etc/(?:shadow|passwd)\b",                      "read /etc sensitive"),

    # NETWORK — remote execution
    (r"\b(?:wget|curl)\b.*\|\s*(?:sh|bash)\b",                "download pipe shell"),
    (r"\bcurl.*\|.*(?:ba)?sh",                                  "curl-pipe-shell"),

    # ACS SELF-PROTECT — tamper detection
    (r"\bchmod\s+.*-[a-z]*x[a-z]*.*acs_",                      "chmod on ACS engine"),
    (r"(?:cat|tee|dd|cp|mv)\s+.*>\s*\S*acs_",                 "ACS tamper: engine"),
    (r"(?:cat|tee|dd)\s+.*>\s*\S*\.claude/(?:hooks|runtime)/", "ACS tamper: hooks/runtime"),
    (r"(?:cat|tee|dd)\s+.*>\s*\S*\.codebuddy/(?:hooks|runtime)/","ACS tamper: codebuddy"),
    (r"rm\s+\S*\.(?:claude|codebuddy)/(?:hooks|runtime|governance)", "ACS tamper: delete"),
    (r"sed\s+-i.*\.(?:claude|codebuddy)/(?:hooks|runtime)",     "ACS tamper: sed"),
]

COMPILED_DANGEROUS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in DANGEROUS_BASH]

# ── Git destructive patterns ────────────────────────────────────────────────

GIT_DESTRUCTIVE: List[Tuple[str, str]] = [
    (r"git\s+restore\s+.*--\s+\.$",            "git restore -- . (uncontrolled overwrite)"),
    (r"git\s+reset\s+--hard",                   "git reset --hard (destroys uncommitted work)"),
    (r"git\s+clean\s+-[fdx]+",                  "git clean (deletes untracked files)"),
    (r"git\s+push\s+--force",                   "git push --force (overwrites remote history)"),
    (r"git\s+push\s+-f\b",                     "git push -f (overwrites remote history)"),
    (r"git\s+checkout\s+--\s+\.",              "git checkout -- . (discards all changes)"),
]

COMPILED_GIT = [(re.compile(p, re.IGNORECASE), desc) for p, desc in GIT_DESTRUCTIVE]


# ── Command cleaning ────────────────────────────────────────────────────────

def clean_command(cmd: str) -> str:
    """Remove content inside quotes, heredocs, and decode content."""
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
    # First pass: check for bypass patterns (before cleaning)
    bypass_patterns = [
        (re.compile(r"\bbase64\s+(?:-d|--decode).*\|.*(?:ba)?sh\b", re.I),
         "base64 decode pipe to shell"),
        (re.compile(r"\bxxd\s+-r\s+-p.*\|.*(?:ba)?sh\b", re.I),
         "xxd decode pipe to shell"),
        (re.compile(r"\bopenssl\s+(?:base64|enc)\s+-d.*\|.*(?:ba)?sh\b", re.I),
         "openssl decode pipe to shell"),
    ]
    for pattern, desc in bypass_patterns:
        if pattern.search(command):
            return f"Dangerous command blocked: {desc}"

    # Second pass: clean command and check all patterns
    cleaned = clean_command(command)

    for pattern, desc in COMPILED_DANGEROUS:
        if pattern.search(cleaned):
            return f"Dangerous command blocked: {desc}"

    for pattern, desc in COMPILED_GIT:
        if pattern.search(command):
            return f"Destructive git blocked: {desc}"

    return None
