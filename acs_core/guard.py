# acs_core/guard.py -- Agent-agnostic Bash and Git guard patterns
# Used by all ACS adapter variants.

import re
from typing import List, Tuple

# -- Dangerous Bash patterns --

DANGEROUS_BASH: List[Tuple[str, str]] = [
    # DELETE
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+/(?:\s|$)",       "rm -rf /"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+/\*",             "rm -rf /*"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+\*",              "rm -rf *"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+~",                "rm -rf ~"),
    (r"(?:^|[|;&]\s*)rm\s+-[a-zA-Z]*[rf]\s+\S*(?:PROJ|REPO|project|repo)\b", "rm -rf project/repo"),
    (r"\btruncate\s+-s\s+0",                                   "truncate to zero"),

    # SYSTEM
    (r"(?:^|[|;&]\s*)kill\s+-9\b",                             "kill -9 (force kill)"),
    (r"(?:^|[|;&]\s*)mkfs\.",                                   "mkfs (disk format)"),
    (r"(?:^|[|;&]\s*)dd\s+if=/dev/",                           "dd writing to block device"),
    (r"\breboot\b",                                             "reboot"),
    (r"\bshutdown\b",                                           "shutdown"),
    (r":\(\s*\)\s*\{",                                         "fork bomb (colon style)"),
    (r"\w+\(\s*\)\s*\{[^}]*\|[^}]*&\s*[^}]*\}",            "fork bomb (named func style)"),

    # EXEC -- inline interpreter
    (r"\b(?:node|python3?|perl|ruby|php|lua)\s+-[ce]\b",      "inline interpreter execution"),
    (r"\b(?:python3?|node|perl|ruby|bash)\s+<<",               "heredoc interpreter"),
    (r"\beval\s+\$",                                            "eval with variable/substitution"),

    # BYPASS -- encoding/decoding pipe chains
    (r"\bbase64\s+(?:-d|--decode).*\|.*(?:ba)?sh\b",         "base64 decode pipe to shell"),
    (r"\bxxd\s+-r\s+-p.*\|.*(?:ba)?sh\b",                    "xxd decode pipe to shell"),
    (r"\bopenssl\s+(?:base64|enc)\s+-d.*\|.*(?:ba)?sh\b",   "openssl decode pipe to shell"),
    (r"\b(?:nc|ncat)\s+.*\|\s*(?:ba)?sh\b",                   "netcat pipe to shell"),
    # Nested decode inside command substitution
    (r"sh\s+-c\s+.*\$\(.*(?:base64|xxd|openssl).*\|\s*(?:ba)?sh", "nested decode in subshell"),
    (r"\bsh\s+-c\s+.*\$\(.*base64.*-d.*\)",                   "sh -c with base64 decode subshell"),
    # Git with variable args (potential indirection)
    (r"\bgit\s+\$\w+\s+\$\w+",                                "git with variable arguments"),
    # Alias definition + execution in same command
    (r"\balias\s+(\w+)=.*;\s*\1\b",                           "alias definition then execution"),

    # WRITE
    (r"\bchmod\s+777\b",                                       "chmod 777"),
    (r"\bchmod\s+(?:-R\s+)?777\s+/(?:etc|usr|bin|sbin|var|tmp|home|root|opt)/",
     "chmod 777 on system path"),
    (r"\bchown\s+root\b",                                      "chown root"),
    (r">\s*/etc/",                                              "overwrite /etc file"),
    (r">\s*/(?:etc|boot)/",                                     "redirect overwrite to system path"),
    # File injection into system directories
    (r"\b(?:mv|cp|install)\s+.*\s+/(?:etc|usr/bin|usr/sbin|bin|sbin|boot)/",
     "file injection into system directory"),
    (r"\bln\s+-s[f]?\s+.*\s+/(?:etc|usr|bin|sbin|boot)/",
     "symlink injection into system directory"),

    # ANTI-FORENSIC
    (r"\bhistory\s+-[cw]\b",                                   "clear shell history"),
    (r"\bunset\s+HISTFILE\b",                                  "disable shell history"),
    (r"\bcat\s+/etc/(?:shadow|passwd)\b",                      "read /etc sensitive"),

    # NETWORK
    (r"\b(?:wget|curl)\b.*\|\s*(?:sh|bash)\b",                "download pipe shell"),
    (r"\bcurl.*\|.*(?:ba)?sh",                                  "curl-pipe-shell"),

    # ACS SELF-PROTECT
    (r"\bchmod\s+.*-[a-z]*x[a-z]*.*acs_",                      "chmod on ACS engine"),
    (r"(?:cat|tee|dd|cp|mv)\s+.*>\s*\S*acs_",                 "ACS tamper: engine"),
    (r"(?:cat|tee|dd)\s+.*>\s*\S*\.claude/(?:hooks|runtime)/", "ACS tamper: hooks/runtime"),
    (r"(?:cat|tee|dd)\s+.*>\s*\S*\.codebuddy/(?:hooks|runtime)/","ACS tamper: codebuddy"),
    (r"rm\s+\S*\.(?:claude|codebuddy)/(?:hooks|runtime|governance)", "ACS tamper: delete"),
    (r"sed\s+-i.*\.(?:claude|codebuddy)/(?:hooks|runtime)",     "ACS tamper: sed"),
]

COMPILED_DANGEROUS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in DANGEROUS_BASH]

# -- Git destructive patterns --

GIT_DESTRUCTIVE: List[Tuple[str, str]] = [
    (r"git\s+restore\s+--\s+\.$",               "git restore -- . (uncontrolled overwrite)"),
    (r"git\s+reset\s+--hard",                   "git reset --hard (destroys uncommitted work)"),
    (r"git\s+clean\s+-[fdx]+",                  "git clean (deletes untracked files)"),
    (r"git\s+push\s+--force(?!-)",               "git push --force (overwrites remote history)"),
    (r"git\s+push\s+-f\b",                     "git push -f (overwrites remote history)"),
    (r"git\s+checkout\s+--\s+\.",              "git checkout -- . (discards all changes)"),
]

COMPILED_GIT = [(re.compile(p, re.IGNORECASE), desc) for p, desc in GIT_DESTRUCTIVE]


# -- Command cleaning --

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


# -- Guard check --

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
        # sh -c with encoded content in subshell (before quote stripping)
        (re.compile(r"\bsh\s+-c\s+.*\$\(.*(?:base64|xxd|openssl).*(?:-d|--decode).*\)", re.I),
         "sh -c with encoded subshell"),
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


def check_bash_with_context(
    command: str,
    asset_ledger=None,
    error_count: int = 0,
) -> dict:
    """Context-aware Bash safety check with tri-state output.

    Args:
        command: The bash command to check
        asset_ledger: Optional AssetLedger for asset-aware decisions
        error_count: Agent's recent error count (for safe mode)

    Returns:
        {"decision": "ALLOW"|"CONFIRM"|"BLOCK", "reason": str}
    """
    # Level 1: Pattern matching
    pattern_result = check_bash(command)
    if pattern_result:
        return {"decision": "BLOCK", "reason": pattern_result}

    # Level 2: Asset-aware check for destructive operations
    if asset_ledger is not None:
        asset_result = _check_asset_safety(command, asset_ledger)
        if asset_result:
            return asset_result

    # Level 3: Post-error safe mode (only upgrades ALLOW -> CONFIRM, never downgrades BLOCK)
    if error_count >= 2 and _is_destructive(command) and result["decision"] == "ALLOW":
        return {
            "decision": "CONFIRM",
            "reason": "safe_mode: agent has 2+ recent errors".format(error_count),
        }

    return {"decision": "ALLOW", "reason": "safe"}


def _is_destructive(command: str) -> bool:
    """Check if a command is potentially destructive (rm, git destructive, etc.)."""
    return bool(re.search(r"\b(?:rm\s+-[rf]|git\s+(?:reset|clean|push|checkout|restore))\b", command))


def _check_asset_safety(command: str, ledger) -> Optional[dict]:
    """Check command against the asset ledger for context-aware safety."""
    import re as _re

    rm_match = _re.search(r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)?(\S+)", command)
    mv_match = _re.search(r"\bmv\s+\S+\s+(\S+)", command)

    is_rm = rm_match is not None
    target_path = rm_match.group(1) if rm_match else (mv_match.group(1) if mv_match else None)

    if target_path is None:
        return None

    if not ledger.is_tracked(target_path):
        return None

    decision = ledger.is_safe_to_delete(target_path)
    if "BLOCK" in decision:
        # rm of critical asset -> BLOCK, mv of critical asset -> CONFIRM
        if is_rm:
            return {"decision": "BLOCK", "reason": "asset_ledger: {}".format(decision)}
        else:
            return {"decision": "CONFIRM", "reason": "asset_ledger: {}".format(decision.replace("BLOCK:", "mv_tracked_asset:"))}
    elif "CONFIRM" in decision:
        return {"decision": "CONFIRM", "reason": "asset_ledger: {}".format(decision)}

    return None
