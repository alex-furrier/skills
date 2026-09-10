"""Exact evidence-boundary facts for historical reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvidenceCompleteness(StrEnum):
    """How much of the declared evidence scope was deterministically established."""

    COMPLETE = "complete"
    BOUNDED = "bounded"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"


class EvidenceScopeKind(StrEnum):
    """The historical scope whose completeness is being described."""

    REPOSITORY = "repository"
    MODULE = "module"
    RECENT_HISTORY = "recent-history"


@dataclass(frozen=True)
class EvidenceLimitation:
    """One exact reason an evidence scope is not complete."""

    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class EvidenceBoundary:
    """Machine-verifiable boundary for a backfill evidence result."""

    completeness: EvidenceCompleteness
    scope_kind: EvidenceScopeKind
    scope_path: str
    cutoff_sha: str
    cutoff_tree: str | None
    repository_roots: tuple[str, ...] = ()
    limitations: tuple[EvidenceLimitation, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "completeness": self.completeness.value,
            "scope": {"kind": self.scope_kind.value, "path": self.scope_path},
            "cutoff_sha": self.cutoff_sha,
            "cutoff_tree": self.cutoff_tree,
            "repository_roots": list(self.repository_roots),
            "limitations": [limitation.to_dict() for limitation in self.limitations],
        }
