"""Stable result models for code-health."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolStatus:
    """Availability and execution state for one evidence producer."""

    tool: str
    status: str
    detail: str
    command: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    """One raw analyzer finding with provenance."""

    tool: str
    rule: str
    metric: str
    path: str
    line: int
    symbol: str
    value: int | None
    threshold: int | None
    message: str
    scope: str
    changed: bool = False
    churn: int = 0

    @property
    def key(self) -> tuple[str, str, str, str]:
        """Return the stable identity used for baseline comparison."""
        location = self.symbol or f"line:{self.line}"
        return (self.path, location, self.metric, self.rule)


@dataclass(frozen=True)
class MetricDelta:
    """Baseline comparison for one stable finding identity."""

    path: str
    symbol: str
    metric: str
    rule: str
    before: int | None
    after: int | None
    status: str
    before_finding: Finding | None = None
    after_finding: Finding | None = None


@dataclass
class Report:
    """Versioned repository analysis result."""

    version: int
    mode: str
    repository: str
    scope: str
    repository_root: str
    revision: str
    base: str | None
    baseline_revision: str | None
    churn_days: int
    working_tree_paths: list[str]
    status: str
    languages: list[str]
    size: dict[str, int]
    summary: dict[str, int]
    findings: list[Finding]
    deltas: list[MetricDelta]
    tools: list[ToolStatus]
    unavailable_metrics: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)
