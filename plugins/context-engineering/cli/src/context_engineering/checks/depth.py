"""Depth-appropriate content checks (P3).

At the repo root, Commands sections are out of place — they should live in
module-level AGENTS.md files. Near the root, deep submodule path references
are a signal that content should have been written at a deeper level.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ..domain.finding import Finding, Severity
from ..domain.result import LintResult
from ..infra.filesystem import read_text_safe
from ..infra.git import git_root

_COMMANDS_SECTIONS = {"commands", "dev commands", "development commands"}
_DEEP_PATH_RE = re.compile(r"`([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-./]+)`")


def compute_depth(agents_path: Path, repo_root: Path) -> int:
    """Depth of AGENTS.md's directory relative to the repo root. -1 if outside."""
    try:
        rel = agents_path.parent.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return -1
    return len([p for p in rel.parts if p != "."])


def _check(path: Path, depth: int) -> Iterator[Finding]:
    content = read_text_safe(path)
    if content is None:
        return

    current_section: str | None = None

    for i, line in enumerate(content.splitlines(), 1):
        if line.startswith("## "):
            current_section = line.lstrip("# ").strip().lower()

            if depth == 0 and current_section in _COMMANDS_SECTIONS:
                yield Finding(
                    file=str(path),
                    line=i,
                    severity=Severity.WARNING,
                    code="P3-depth0-commands",
                    message="Commands section at repo root (depth 0)",
                    hint="Defer dev commands to module-level AGENTS.md files",
                )
                continue

        if depth <= 1:
            for ref in _DEEP_PATH_RE.findall(line):
                if ref.startswith("http") or ".." in ref:
                    continue
                yield Finding(
                    file=str(path),
                    line=i,
                    severity=Severity.WARNING,
                    code="P3-too-specific",
                    message=f"Reference to `{ref}` may be too specific for depth {depth}",
                    hint="Consider moving to a deeper AGENTS.md",
                )


def lint(target: Path) -> LintResult:
    """Lint an AGENTS.md.

    Accepts either a file path or a directory. For a directory, we lint
    `<dir>/AGENTS.md` if it exists (quick-start mode when AGENTS.md doesn't
    exist yet returns empty findings — depth is implicit in the target).
    """
    repo = git_root(target)
    agents = target / "AGENTS.md" if target.is_dir() else target
    depth = compute_depth(agents, repo) if repo else -1

    if depth < 0 or not agents.is_file():
        return LintResult(target=str(agents), findings=[])

    return LintResult(target=str(agents), findings=list(_check(agents, depth)))
