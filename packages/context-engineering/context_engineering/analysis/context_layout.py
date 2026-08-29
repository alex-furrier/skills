"""Discover portable repository context owners from current filesystem truth."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..infra.filesystem import EXCLUDED_DIRS

_ADR_NAMES = {"adr", "adrs", "decisions"}
_ADR_PARENTS = {"architecture", "docs"}
_AGENT_TEMPLATE_ROOTS = ((".ai", "plans", "_templates"),)


def is_ignored_contract_path(path: Path) -> bool:
    """Return whether a repository-relative path is an agent template artifact."""
    return any(path.parts[: len(root)] == root for root in _AGENT_TEMPLATE_ROOTS)


@dataclass(frozen=True)
class ContextTree:
    path: Path
    framework: str | None = None


@dataclass(frozen=True)
class RepositoryContextLayout:
    root: Path
    contract_roots: tuple[Path, ...]
    specs: tuple[Path, ...]
    adr_trees: tuple[ContextTree, ...]
    docs_trees: tuple[ContextTree, ...]
    agents_files: tuple[Path, ...]
    skill_roots: tuple[Path, ...]


def _sort_paths(paths: set[Path]) -> tuple[Path, ...]:
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def _docs_framework(path: Path) -> str | None:
    """Return the framework that owns a docs tree, when one is evidenced."""
    parent = path.parent
    markers = (
        (parent / "mkdocs.yml", "mkdocs"),
        (parent / "mkdocs.yaml", "mkdocs"),
        (parent / "docusaurus.config.js", "docusaurus"),
        (parent / "docusaurus.config.ts", "docusaurus"),
        (path / "conf.py", "sphinx"),
        (parent / "book.toml", "mdbook"),
    )
    return next((framework for marker, framework in markers if marker.is_file()), None)


def discover(root: Path) -> RepositoryContextLayout:
    """Return one conservative layout consumed by context checks and review."""
    root = root.resolve()
    directories: set[Path] = set()
    specs: set[Path] = set()
    agents_files: set[Path] = set()
    docs_trees: set[Path] = set()
    skill_roots: set[Path] = set()
    for current_text, names, files in os.walk(root):
        current = Path(current_text)
        names[:] = sorted(
            name
            for name in names
            if name not in EXCLUDED_DIRS and (not name.startswith(".") or name == ".agents")
        )
        directories.add(current)
        if current.name == "docs" and "docs" not in current.relative_to(root).parts[:-1]:
            docs_trees.add(current)
        if current.name == "skills":
            skill_roots.add(current)
        if "SPEC.md" in files:
            spec = current / "SPEC.md"
            if not is_ignored_contract_path(spec.relative_to(root)):
                specs.add(spec)
        if "AGENTS.md" in files:
            agents_files.add(current / "AGENTS.md")

    spec_roots = {spec.parent for spec in specs}
    adr_trees = {
        directory
        for directory in directories
        if directory != root
        and directory.name.casefold() in _ADR_NAMES
        and (
            directory.parent == root
            or directory.parent.name.casefold() in _ADR_PARENTS
            or directory.parent in spec_roots
        )
    }
    contract_roots = {root, *spec_roots}
    for tree in adr_trees:
        if tree.parent.name.casefold() in _ADR_PARENTS:
            contract_roots.add(tree.parent.parent)
        else:
            contract_roots.add(tree.parent)
    return RepositoryContextLayout(
        root=root,
        contract_roots=_sort_paths(contract_roots),
        specs=_sort_paths(specs),
        adr_trees=tuple(ContextTree(path) for path in _sort_paths(adr_trees)),
        docs_trees=tuple(
            ContextTree(path, framework=_docs_framework(path)) for path in _sort_paths(docs_trees)
        ),
        agents_files=_sort_paths(agents_files),
        skill_roots=_sort_paths(skill_roots),
    )
