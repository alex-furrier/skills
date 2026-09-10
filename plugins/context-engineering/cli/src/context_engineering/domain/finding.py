"""Finding — the one warning/error type every linter emits."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, order=False)
class Finding:
    file: str
    line: int
    severity: Severity
    code: str
    message: str
    hint: str | None = field(default=None)

    def __lt__(self, other: Finding) -> bool:
        return (self.file, self.line, self.code) < (other.file, other.line, other.code)

    def to_dict(self) -> dict:
        payload = {
            "file": self.file,
            "line": self.line,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
        }
        if self.hint is not None:
            payload["hint"] = self.hint
        return payload
