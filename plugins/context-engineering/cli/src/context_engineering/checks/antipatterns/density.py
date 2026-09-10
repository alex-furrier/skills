"""P2: section density — long prose with no file refs or DO/NOT/BECAUSE bullets.

Heuristic: an H2 section with 5+ prose lines and no file:line references and no
DO/NOT/BECAUSE markers is drifting architecture prose that belongs in docs/.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ...domain.finding import Finding, Severity
from ...infra.filesystem import read_text_safe
from .context import CheckContext

_FILE_REF_RE = re.compile(r"`[^`]+:\d+`|`[^`]+\.[a-z]+`")
_MARKER_RE = re.compile(r"\*\*DO\*\*|\*\*NOT\*\*|\*\*BECAUSE\*\*")
_MIN_PROSE = 5


def _is_prose(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith(("#", "-", "*", "|", ">", "```"))


def _evaluate_section(
    path: Path, section: str, start_line: int, body: list[str]
) -> Iterator[Finding]:
    prose = [ln for ln in body if _is_prose(ln)]
    if len(prose) <= _MIN_PROSE:
        return
    if any(_FILE_REF_RE.search(ln) for ln in body):
        return
    if any(_MARKER_RE.search(ln) for ln in body):
        return
    yield Finding(
        file=str(path),
        line=start_line,
        severity=Severity.INFO,
        code="P2-low-density",
        message=(
            f"Section '{section}' has {len(prose)} prose lines with no "
            "file:line references or DO/NOT/BECAUSE bullets"
        ),
        hint="Consider cutting, adding specific references, or moving to docs/",
    )


def check(path: Path, _ctx: CheckContext) -> Iterator[Finding]:
    if path.name not in ("AGENTS.md", "CLAUDE.md"):
        return
    content = read_text_safe(path)
    if content is None:
        return

    current: str | None = None
    start = 0
    body: list[str] = []

    for i, line in enumerate(content.splitlines(), 1):
        if line.startswith("## "):
            if current is not None:
                yield from _evaluate_section(path, current, start, body)
            current = line.lstrip("# ").strip()
            start = i
            body = []
        elif current is not None:
            body.append(line)

    if current is not None:
        yield from _evaluate_section(path, current, start, body)
