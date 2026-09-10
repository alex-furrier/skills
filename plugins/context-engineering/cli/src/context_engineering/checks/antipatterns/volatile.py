"""P4: flag content that goes stale quickly (counts, timestamps, versions)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ...domain.finding import Finding, Severity
from ...infra.filesystem import read_text_safe
from .context import CheckContext

_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(
        r"~?\d{2,}\s+(files?|dirs?|directories|modules?|models?|services?|"
        r"tables?|tests?|endpoints?|routes?|components?|packages?)"
    ), "volatile count"),
    (re.compile(r"[Aa]ll\s+\d+\s+\w+"), "volatile count with 'all'"),
    (re.compile(r"Updated:\s*\d{4}-\d{2}-\d{2}"), "diagram timestamp (stale quickly)"),
    (re.compile(r"v\d+\.\d+\.\d+"), "version number (may go stale)"),
)


def check(path: Path, _ctx: CheckContext) -> Iterator[Finding]:
    content = read_text_safe(path)
    if content is None:
        return
    for i, line in enumerate(content.splitlines(), 1):
        for pattern, message in _PATTERNS:
            if pattern.search(line):
                yield Finding(
                    file=str(path),
                    line=i,
                    severity=Severity.WARNING,
                    code="P4-volatile",
                    message=message,
                    hint=line.strip()[:100],
                )
