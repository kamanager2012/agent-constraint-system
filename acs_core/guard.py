# acs_core/guard.py -- Agent-agnostic Bash and Git guard patterns
# Used by all ACS adapter variants.

import re
from typing import List, Optional, Tuple

# -- Dangerous Bash patterns --

# ACS self-protect: one source of truth for agent dirs + protected subdirs.
# Mirrors paths.AGENT_BASE_DIRS / paths.AGENT_PROTECTED_SUBDIRS so the Bash
# guard and the Write guard block exactly the same locations.
_AGENT = r"(?:claude|codebuddy|codex|cursor|gemini|grok|hermes|opencode|qoder-cn|acs_core)"
_AGENT_SUB = r"(?:hooks|runtime|governance|agent-hooks|cacs_runtime|gacs_runtime|grok_acs_runtime|hacs_runtime|qacs_runtime)"

DANGEROUS_BASH: List[Tuple[str, str]] = [
    # DELETE
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*)\s*rm\s+-[a-zA-Z]*[rf]\s+/(?:\s|$)",       "rm -rf /"),
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*)\s*rm\s+-[a-zA-Z]*[rf]\s+/\*",             "rm -rf /*"),
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*)\s*rm\s+-[a-zA-Z]*[rf]\s+\*",              "rm -rf *"),
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*)\s*rm\s+-[a-zA-Z]*[rf]\s+~",                "rm -rf ~"),
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*)\s*rm\s+-[a-zA-Z]*[rf]\s+\S*(?:PROJ|REPO|project|repo)\b", "rm -rf project/repo"),
    (r"\btruncate\s+-s\s+0",                                   "truncate to zero"),
    # FIND with delete/exec (bypasses rm -rf pattern checks)
    (r"\bfind\b.*\s+-exec\s+(?:rm|sh|bash|python)\b",            "find -exec (dangerous)"),
    (r"\bfind\b.*\s+-delete\b",                                   "find -delete (destroys files)"),
    # xargs with dangerous commands
    (r"\bxargs\b.*\brm\s+-[rf]",                                "xargs rm (via pipeline)"),

    # SYSTEM
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*|sudo\s+|exec\s+|env\s+|nice\s+|command\s+)*\s*kill\s+-9\b",  "kill -9 (force kill)"),
    (r"\bmkfs(?:\.\w+|\s+-t\s+\w+)",                            "mkfs (disk format)"),
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*|sudo\s+|exec\s+|env\s+|nice\s+|command\s+)*\s*dd\s+if=/dev/","dd writing to block device"),
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
    # Alternative decoders (Python, Perl, Ruby)
    (r"\b(?:python3?|perl|ruby)\s+-[ce]\s+(?:import\s+base64|MIME::Base64|Base64)", "scripted base64 decode"),
    (r"\bpython3?\s+-c\s+.*base64.*\.decode\(",               "python base64 decode"),
    # Nested decode inside command substitution
    (r"sh\s+-c\s+.*\$\(.*(?:base64|xxd|openssl).*\|\s*(?:ba)?sh", "nested decode in subshell"),
    (r"\bsh\s+-c\s+.*\$\(.*base64.*-d.*\)",                   "sh -c with base64 decode subshell"),
    # Git with variable args (potential indirection)
    (r"\bgit\s+\$\w+\s+\$\w+",                                "git with variable arguments"),
    # Alias definition + execution in same command
    (r"\balias\s+(\w+)=.*;\s*\1\b",                           "alias definition then execution"),
    # EVAL bypass: eval with any substitution mechanism
    (r"\beval\s+(?:\$\(|`|\"|\$)\S*",                         "eval with substitution (potential bypass)"),

    # WRITE
    (r"\bchmod\s+777\b",                                       "chmod 777"),
    (r"\bchmod\s+(?:-R\s+)?777\s+/(?:etc|usr|bin|sbin|var|tmp|home|root|opt)/",
     "chmod 777 on system path"),
    (r"\bchown\s+root\b",                                      "chown root"),
    (r">\s*/etc/",                                              "overwrite /etc file"),
    (r">\s*/(?:etc|boot)/",                                     "redirect overwrite to system path"),
    (r"\bsed\b\s+-i\b",                                       "sed -i (WSL in-place edit, rename race risk)"),
    (r"\bsed\b\s+--in-place\b",                               "sed --in-place (WSL truncation risk)"),
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

    # ── ACS SELF-PROTECT ── covers ALL 9 supported agent runtime/hooks dirs ──
    # Agent base dirs + protected subdirs (kept here so every pattern below
    # shares one source of truth; see also paths.AGENT_BASE_DIRS).
    (r"\bchmod\s+.*-[a-z]*x[a-z]*.*(?:acs_|" + _AGENT + r")", "chmod on ACS engine"),
    (r"(?:cat|tee|dd|cp|mv)\s+.*>\s*\S*(?:acs_|" + _AGENT + r"/)", "ACS tamper: engine"),
    # Redirect (echo/cat/tee/dd >, including >>) into any agent runtime/hooks dir
    (r">>?\s*\S*?\." + _AGENT + r"/" + _AGENT_SUB, "ACS tamper: redirect into runtime/hooks"),
    # Destructive file ops (rm/mv/cp/truncate/shred) on agent runtime/hooks dirs.
    # NOTE: .*? (not \S*) so it survives the space inside "rm -rf /path".
    (r"\b(?:rm|mv|cp|truncate|shred)\b(?:\s+-[a-zA-Z]+)*\s+.*?\.?" + _AGENT + r"/" + _AGENT_SUB,
     "ACS tamper: agent runtime/hooks"),
    # in-place edit of agent runtime/hooks files
    (r"\bsed\b\s+-i\b.*?\.?" + _AGENT + r"/" + _AGENT_SUB, "ACS tamper: sed -i agent dir"),
    # symlink injection into agent runtime/hooks
    (r"\bln\s+-s[f]?\s+.*?\.?" + _AGENT + r"/" + _AGENT_SUB, "ACS tamper: symlink into agent dir"),
    # Absolute-path rm bypass for destructive commands
    (r"(?:^|[|;&]|\s*&&\s*|\s*\|\|\s*|sudo\s+|exec\s+|env\s+|nice\s+)\s*(?:/usr)?/bin/rm\s+-[a-zA-Z]*[rf]\s+/",
     "rm via absolute path"),
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
    (r"git\s+branch\s+-[dD]\s+(?:main|master)\b", "git branch -d/D main/master (protected)"),
    (r"git\s+branch\s+-[mM]\s+(?:main|master)\b", "git branch -m/M main/master (protected)"),
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


# -- Command splitting --

def _split_commands(cmd: str) -> list[str]:
    """Split command on shell chaining operators (&&, ||, ;, |, newline)
    into individual sub-commands. Each sub-command is checked independently
    to prevent bypasses like "true && rm -rf /".
    """
    # Split preserving | for pipe chains (we check the whole pipe)
    # But split on command separators: &&, ||, ;, newlines
    parts = re.split(r'\s*&&\s*|\s*\|\|\s*|[;&]\s*|\n', cmd)
    return [p.strip() for p in parts if p.strip()]


def _strip_prefix(cmd: str) -> str:
    """Strip privilege elevation and environment prefixes from command."""
    return re.sub(r'^(?:sudo|exec|env|nice|ionice|nohup|command|time)\s+', '', cmd, count=3)


# -- Guard check --

# Patterns that MUST see the whole (un-split) command. Fork bombs and
# alias-definition-then-exec contain ; & | *inside* them, which the
# sub-command splitter would otherwise shred and let through.
_WHOLE_CMD_PATTERNS = [
    (re.compile(r"\w+\(\s*\)\s*\{[^}]*\|[^}]*&\s*[^}]*\}", re.I),
     "fork bomb (named func style)"),
    (re.compile(r":\(\s*\)\s*\{", re.I),
     "fork bomb (colon style)"),
    (re.compile(r"\balias\s+\w+=.*;\s*\w+\b", re.I),
     "alias definition then execution"),
]

# Compiled once at import time (was recompiled on every check_bash call)
_BYPASS_PATTERNS = [
    (re.compile(r"\bbase64\s+(?:-d|--decode).*\|.*(?:ba)?sh\b", re.I),
     "base64 decode pipe to shell"),
    (re.compile(r"\bxxd\s+-r\s+-p.*\|.*(?:ba)?sh\b", re.I),
     "xxd decode pipe to shell"),
    (re.compile(r"\bopenssl\s+(?:base64|enc)\s+-d.*\|.*(?:ba)?sh\b", re.I),
     "openssl decode pipe to shell"),
    # sh -c with encoded content in subshell (before quote stripping)
    (re.compile(r"\bsh\s+-c\s+.*\$\(.*(?:base64|xxd|openssl).*(?:-d|--decode).*\)", re.I),
     "sh -c with encoded subshell"),
    # Alternative decoders: python/perl with base64 (before quote stripping)
    (re.compile(r"\b(?:python3?|perl|ruby)\s+-[ce].*(?:base64|MIME::Base64|\.decode\()", re.I),
     "scripted base64 decode"),
    # Variable indirection: $VAR containing dangerous paths
    (re.compile(r"\b(?:export\s+)?\w+\s*=\s*(?:rm|dd|mkfs|kill|chmod)\b", re.I),
     "variable assignment of dangerous command"),
    # eval with sub-shell (potential full bypass)
    (re.compile(r"\beval\s+(?:\$\(|`|\")", re.I),
     "eval with substitution (potential bypass)"),
]


def check_bash(command: str) -> str | None:
    """Check a Bash command against all dangerous patterns.

    Returns the blocking reason if dangerous, None if safe.
    """
    # First pass: check for bypass patterns (before cleaning — encoded content in quotes)
    for pattern, desc in _BYPASS_PATTERNS:
        if pattern.search(command):
            return f"Dangerous command blocked: {desc}"

    # Whole-command pass: fork bombs / alias-def-exec contain ; & | inside
    # them, so they must be matched before sub-command splitting.
    for pattern, desc in _WHOLE_CMD_PATTERNS:
        if pattern.search(command):
            return f"Dangerous command blocked: {desc}"

    # Split into sub-commands (handles &&, ||, ; chaining bypasses)
    sub_commands = _split_commands(command)

    for sub_cmd in sub_commands:
        # Strip privilege prefixes (sudo, exec, env, etc.)
        stripped = _strip_prefix(sub_cmd)

        # Clean and check each sub-command independently
        cleaned = clean_command(stripped)

        for pattern, desc in COMPILED_DANGEROUS:
            if pattern.search(cleaned):
                return f"Dangerous command blocked: {desc}"

        # Also check original (un-stripped) for patterns that look for prefix contexts
        cleaned_orig = clean_command(sub_cmd)
        for pattern, desc in COMPILED_DANGEROUS:
            if pattern.search(cleaned_orig) and pattern.search(cleaned) is None:
                return f"Dangerous command blocked: {desc}"

        # Git patterns run on cleaned command
        for pattern, desc in COMPILED_GIT:
            if pattern.search(cleaned):
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
    # If we reached here, Level 1 and Level 2 both passed (would be ALLOW).
    if error_count >= 2 and _is_destructive(command):
        return {
            "decision": "CONFIRM",
            "reason": "safe_mode: agent has 2+ recent errors".format(error_count),
        }

    return {"decision": "ALLOW", "reason": "safe"}


def _is_destructive(command: str) -> bool:
    """Check if a command is potentially destructive (rm, git destructive, etc.)."""
    return bool(re.search(r"\b(?:rm\s+-[a-zA-Z]*[rf][a-zA-Z]*|git\s+(?:reset|clean|push|checkout|restore))\b", command))


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
