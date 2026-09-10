"""P11: depth-tiered line limits for AGENTS.md and docs/ files."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ...domain.finding import Finding, Severity
from ...infra.filesystem import read_text_safe
from .context import CheckContext

LIMITS: dict[str, tuple[int, int]] = {
    "depth_0_agents": (80, 120),
    "depth_1_agents": (150, 200),
    "depth_2plus_agents": (250, 300),
    "docs": (300, 500),
}


def _limits_for(path: Path, depth: int) -> tuple[tuple[int, int], str]:
    is_docs = "docs" in path.parts and path.name not in ("AGENTS.md", "README.md")
    if is_docs:
        return LIMITS["docs"], "docs/ file"
    if depth == 0:
        return LIMITS["depth_0_agents"], "root AGENTS.md (depth 0)"
    if depth == 1:
        return LIMITS["depth_1_agents"], f"module AGENTS.md (depth {depth})"
    return LIMITS["depth_2plus_agents"], f"leaf AGENTS.md (depth {depth})"


def check(path: Path, ctx: CheckContext) -> Iterator[Finding]:
    content = read_text_safe(path)
    if content is None:
        return
    line_count = len(content.splitlines())
    depth = ctx.depth(path)
    (target, hard_stop), label = _limits_for(path, depth)

    if line_count > hard_stop:
        yield Finding(
            file=str(path), line=line_count, severity=Severity.WARNING,
            code="P11-size-hard-stop",
            message=f"{label} exceeds hard stop: {line_count}L > {hard_stop}L",
            hint=f"target: {target}, hard stop: {hard_stop}",
        )
    elif line_count > target:
        yield Finding(
            file=str(path), line=line_count, severity=Severity.INFO,
            code="P11-size-warning",
            message=f"{label} exceeds target: {line_count}L > {target}L (hard stop: {hard_stop})",
            hint=f"target: {target}, hard stop: {hard_stop}",
        )
