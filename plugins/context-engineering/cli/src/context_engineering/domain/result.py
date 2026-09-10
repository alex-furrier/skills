"""Result containers — LintResult (findings) and AnalysisResult (data + findings)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .finding import Finding, Severity


@dataclass
class LintResult:
    target: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "findings": [f.to_dict() for f in self.findings],
            "summary": {
                "error": self.error_count,
                "warning": self.warning_count,
                "info": self.info_count,
            },
        }


@dataclass
class AnalysisResult:
    target: str
    data: dict[str, Any] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(finding.severity == Severity.ERROR for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "data": self.data,
            "findings": [f.to_dict() for f in self.findings],
        }
