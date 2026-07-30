# acs_core/capability_ledger.py -- Capability Preservation Ledger
#
# Tracks hardcoded credentials the running code depends on, so an agent cannot
# delete/clear/relocate them before a verified replacement is in place. Mirrors
# AssetLedger (dataclass + atomic JSON persistence + tri-state decision) and
# VerifiedCopyProtocol (verification gate).
#
# State machine:
#   ACTIVE_HARDCODED_SECRET
#       │  (replacement source configured, e.g. env var detected)
#       ▼
#   REPLACEMENT_CONFIGURED
#       │  (replacement credential loads + authenticates)
#       ▼
#   REPLACEMENT_VERIFIED
#       │  (a dependent workflow smoke-test passes using the new source)
#       ▼
#   DEPENDENT_WORKFLOW_PASSED
#       │  (old credential no longer referenced by any code path)
#       ▼
#   OLD_SECRET_REMOVABLE   ──> delete/clear/relocate ALLOWed
#
# Decision gate (removal_decision):
#   ACTIVE_HARDCODED_SECRET / REPLACEMENT_CONFIGURED → BLOCK
#   REPLACEMENT_VERIFIED                              → CONFIRM (no smoke test yet)
#   DEPENDENT_WORKFLOW_PASSED / OLD_SECRET_REMOVABLE → ALLOW

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class CapabilityEntry:
    """A single tracked credential's lifecycle record."""
    path: str
    secret_id: str                                   # e.g. "OPENAI_API_KEY"
    state: str = "ACTIVE_HARDCODED_SECRET"
    replacement_source: Optional[str] = None         # e.g. "env:OPENAI_API_KEY"
    verified_at: Optional[float] = None              # timestamp of REPLACEMENT_VERIFIED
    smoke_test: Optional[str] = None                 # command run at DEPENDENT_WORKFLOW_PASSED
    dependents: List[str] = field(default_factory=list)  # code paths referencing this secret
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return asdict(self)


# Valid state transitions (enforced by the mark_* methods).
_VALID_STATES = {
    "ACTIVE_HARDCODED_SECRET",
    "REPLACEMENT_CONFIGURED",
    "REPLACEMENT_VERIFIED",
    "DEPENDENT_WORKFLOW_PASSED",
    "OLD_SECRET_REMOVABLE",
}


class CapabilityLedger:
    """Tracks hardcoded credentials so their removal is gated on a verified
    replacement, preventing silent runtime capability loss.

    Usage:
        ledger = CapabilityLedger()
        ledger.track(".env", secret_id="OPENAI_API_KEY", dependents=["src/api.py"])
        ledger.removal_decision(".env")   # -> "BLOCK: credential_dependency_unsatisfied"
        ledger.mark_removable(".env")
        ledger.removal_decision(".env")   # -> "ALLOW: ..."
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._caps: Dict[str, CapabilityEntry] = {}
        self._storage_path = storage_path
        if storage_path and os.path.exists(storage_path):
            self._load()

    # -- Tracking --

    def track(self, path: str, secret_id: str, dependents: Optional[List[str]] = None) -> CapabilityEntry:
        """Register a hardcoded credential the code depends on."""
        resolved = str(Path(path).resolve())
        if resolved in self._caps:
            entry = self._caps[resolved]
            entry.updated_at = time.time()
            return entry
        entry = CapabilityEntry(
            path=resolved,
            secret_id=secret_id,
            dependents=list(dependents) if dependents else [],
        )
        self._caps[resolved] = entry
        self._save()
        return entry

    def untrack(self, path: str) -> None:
        """Remove a credential from the ledger (after verified safe removal)."""
        resolved = str(Path(path).resolve())
        self._caps.pop(resolved, None)
        self._save()

    # -- State machine transitions --

    def mark_replacement_configured(self, path: str, replacement_source: str) -> CapabilityEntry:
        """Replacement source configured (e.g. env var detected). Still BLOCK —
        replacement not yet proven to load/authenticate."""
        entry = self._require(path)
        entry.state = "REPLACEMENT_CONFIGURED"
        entry.replacement_source = replacement_source
        entry.updated_at = time.time()
        self._save()
        return entry

    def mark_replacement_verified(self, path: str) -> CapabilityEntry:
        """Replacement credential loads + authenticates. Drops to CONFIRM — a
        dependent workflow smoke-test is still required before removal."""
        entry = self._require(path)
        entry.state = "REPLACEMENT_VERIFIED"
        entry.verified_at = time.time()
        entry.updated_at = time.time()
        self._save()
        return entry

    def mark_workflow_passed(self, path: str, smoke_test: str) -> CapabilityEntry:
        """A dependent workflow smoke-test passed using the new source."""
        entry = self._require(path)
        entry.state = "DEPENDENT_WORKFLOW_PASSED"
        entry.smoke_test = smoke_test
        entry.updated_at = time.time()
        self._save()
        return entry

    def mark_removable(self, path: str) -> CapabilityEntry:
        """Old credential no longer referenced by any code path — safe to remove."""
        entry = self._require(path)
        entry.state = "OLD_SECRET_REMOVABLE"
        entry.updated_at = time.time()
        self._save()
        return entry

    # -- Queries --

    def get(self, path: str) -> Optional[CapabilityEntry]:
        resolved = str(Path(path).resolve())
        return self._caps.get(resolved)

    def is_tracked(self, path: str) -> bool:
        return self.get(path) is not None

    def removal_decision(self, path: str) -> str:
        """Check whether a depended-on credential may be removed.

        Returns one of:
            "ALLOW"                          -- untracked, or replacement fully verified
            "CONFIRM: ..."                   -- needs human confirmation
            "BLOCK: ..."                     -- removal would break runtime capability
        """
        entry = self.get(path)
        if entry is None:
            return "ALLOW"  # not a tracked credential — not our concern

        if entry.state in ("ACTIVE_HARDCODED_SECRET", "REPLACEMENT_CONFIGURED"):
            return "BLOCK: credential_dependency_unsatisfied"
        if entry.state == "REPLACEMENT_VERIFIED":
            return "CONFIRM: replacement_verified_pending_smoke_test"
        # DEPENDENT_WORKFLOW_PASSED or OLD_SECRET_REMOVABLE
        return "ALLOW: replacement_verified_workflow_passed"

    # -- I/O --

    def _require(self, path: str) -> CapabilityEntry:
        resolved = str(Path(path).resolve())
        entry = self._caps.get(resolved)
        if entry is None:
            raise KeyError(f"capability not tracked: {path}")
        return entry

    def _save(self) -> None:
        if self._storage_path:
            data = {k: v.to_dict() for k, v in self._caps.items()}
            os.makedirs(os.path.dirname(self._storage_path) or ".", exist_ok=True)
            # Atomic write: tmp file + rename prevents corruption from concurrent writers
            tmp_path = self._storage_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self._storage_path)

    def _load(self) -> None:
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            for k, v in data.items():
                # Tolerate older entries missing new fields
                v.setdefault("dependents", [])
                v.setdefault("smoke_test", None)
                v.setdefault("verified_at", None)
                v.setdefault("replacement_source", None)
                self._caps[k] = CapabilityEntry(**v)
        except (json.JSONDecodeError, FileNotFoundError, TypeError):
            pass

    def clear(self) -> None:
        """Clear all tracked credentials."""
        self._caps.clear()
        if self._storage_path and os.path.exists(self._storage_path):
            os.remove(self._storage_path)
