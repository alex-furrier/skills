"""Watermark presence + staleness checks.

Presence: AGENTS.md needs an HTML-comment watermark; docs/*.md need both
`generated-by` and `last-updated` frontmatter keys together.

Staleness: a modified file whose `last-updated` date matches HEAD was
"edited without updating the watermark" — a common oversight.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from pathlib import Path

from ...domain.finding import Finding, Severity
from ...infra.filesystem import read_text_safe
from .context import CheckContext

_DATE_RE = re.compile(r"last-updated:\s*(\d{4}-\d{2}-\d{2})")
_HTML_WATERMARK_RE = re.compile(r"<!--\s*generated-by:")


def _last_updated(content: str) -> str | None:
    m = _DATE_RE.search(content)
    return m.group(1) if m else None


def _head_content(path: Path, git_root: Path | None) -> str | None:
    if git_root is None:
        return None
    try:
        rel = path.resolve().relative_to(git_root.resolve())
    except ValueError:
        return None
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=git_root,
        )
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 else None


def check_presence(path: Path, _ctx: CheckContext) -> Iterator[Finding]:
    content = read_text_safe(path)
    if content is None:
        return
    lines = content.splitlines()

    if path.name == "AGENTS.md" and content.startswith("---\n"):
        yield Finding(
            file=str(path), line=1, severity=Severity.WARNING,
            code="structural", message="AGENTS.md should not have YAML frontmatter",
            hint="---",
        )

    has_generated_by = any("generated-by:" in ln for ln in lines)
    has_last_updated = any("last-updated:" in ln for ln in lines)

    if path.name == "AGENTS.md":
        if not _HTML_WATERMARK_RE.search(content):
            yield Finding(
                file=str(path), line=max(1, len(lines)), severity=Severity.WARNING,
                code="watermark-missing",
                message="AGENTS.md missing generated-by HTML comment watermark",
                hint="<!-- generated-by: plugin@version | last-updated: YYYY-MM-DD -->",
            )
        return

    if path.name == "README.md" or path.suffix != ".md":
        return

    if has_generated_by and not has_last_updated:
        yield Finding(
            file=str(path), line=1, severity=Severity.WARNING,
            code="watermark-incomplete",
            message="has generated-by but missing last-updated",
        )
    elif has_last_updated and not has_generated_by:
        yield Finding(
            file=str(path), line=1, severity=Severity.WARNING,
            code="watermark-incomplete",
            message="has last-updated but missing generated-by",
        )


def check_staleness(path: Path, ctx: CheckContext) -> Iterator[Finding]:
    if not ctx.modified_only:
        return
    content = read_text_safe(path)
    if content is None:
        return
    current = _last_updated(content)
    if current is None:
        return
    head = _head_content(path, ctx.git_root)
    if head is None:
        return
    head_date = _last_updated(head)
    if head_date is None or head_date != current:
        return
    line_num = next(
        (i for i, ln in enumerate(content.splitlines(), 1) if "last-updated:" in ln),
        1,
    )
    yield Finding(
        file=str(path), line=line_num, severity=Severity.WARNING,
        code="watermark-stale",
        message=f"file was modified but last-updated date unchanged ({current})",
        hint=f"Update last-updated to today's date (currently: {current})",
    )
