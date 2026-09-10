"""Compose the 5 antipattern checkers over a discovered file set."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from ...domain.finding import Finding
from ...domain.result import LintResult
from ...infra.filesystem import EXCLUDED_DIRS
from ...infra.git import git_root
from . import density, line_limits, splitting, volatile, watermark
from .context import CheckContext

# Checker signature: (path, ctx) -> Iterator[Finding]
Checker = Callable[[Path, CheckContext], Iterator[Finding]]

# Universal checkers — run on every candidate file.
UNIVERSAL: tuple[Checker, ...] = (
    volatile.check,
    watermark.check_presence,
    watermark.check_staleness,
    density.check,
)

# Checkers that apply only to AGENTS.md / CLAUDE.md
AGENTS_ONLY: tuple[Checker, ...] = (
    line_limits.check,
    splitting.check,
)

# Checkers that apply only to docs/*.md (non-AGENTS, non-README)
DOCS_ONLY: tuple[Checker, ...] = (
    line_limits.check,
)


def _is_candidate(path: Path) -> bool:
    if any(p in EXCLUDED_DIRS for p in path.parts):
        return False
    return (
        path.name == "AGENTS.md"
        or path.name == "CLAUDE.md"
        or "docs" in path.parts
    )


def _git_tracked_md(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
            capture_output=True, text=True, cwd=root,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [root / p for p in result.stdout.strip().splitlines() if p]


def _git_modified_md(root: Path, gr: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-u"],
            capture_output=True, text=True, cwd=root,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    files: list[Path] = []
    for line in result.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path_str = line[3:].strip()
        if " -> " in path_str:
            path_str = path_str.split(" -> ")[-1]
        if not path_str.endswith(".md"):
            continue
        full = (gr / path_str).resolve()
        try:
            full.relative_to(root.resolve())
            files.append(full)
        except ValueError:
            continue
    return files


def _filesystem_fallback(root: Path) -> Iterable[Path]:
    """Used outside git — targeted walk, not full rglob."""
    if (root / "AGENTS.md").exists():
        yield root / "AGENTS.md"
    docs = root / "docs"
    if docs.is_dir():
        yield from sorted(docs.rglob("*.md"))
    for child in sorted(root.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            nested = child / "AGENTS.md"
            if nested.exists():
                yield nested


def _discover(root: Path, gr: Path | None, modified_only: bool) -> list[Path]:
    if modified_only and gr is not None:
        return _git_modified_md(root, gr)
    candidates = _git_tracked_md(root) if gr is not None else []
    if not candidates and not modified_only:
        candidates = list(_filesystem_fallback(root))
    return candidates


def _checkers_for(path: Path) -> Iterable[Checker]:
    yield from UNIVERSAL
    if path.name in ("AGENTS.md", "CLAUDE.md"):
        yield from AGENTS_ONLY
    elif "docs" in path.parts and path.name != "README.md":
        yield from DOCS_ONLY


def lint(root: Path, *, modified_only: bool = False) -> LintResult:
    gr = git_root(root)
    ctx = CheckContext(root=root, git_root=gr, modified_only=modified_only)

    seen: set[Path] = set()
    findings: list[Finding] = []
    for path in _discover(root, gr, modified_only):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in seen or not _is_candidate(path):
            continue
        seen.add(resolved)
        for checker in _checkers_for(path):
            findings.extend(checker(path, ctx))

    return LintResult(target=str(root), findings=findings)
