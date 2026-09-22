"""Validate YAML frontmatter on docs/*.md content files."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from ..analysis.context_layout import discover
from ..domain.finding import Finding, Severity
from ..domain.result import LintResult
from ..infra.filesystem import EXCLUDED_DIRS, read_text_safe
from ..infra.markdown import mask_invisible_markdown
from ..infra.yaml_frontmatter import parse_frontmatter

_REQUIRED_FIELDS = ("id", "title", "description")
_HEADING_RE = re.compile(r"^##\s+(.+?)(?:\s*\{.*\})?\s*$")


def _slugify(heading: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")


def _h2_slugs(body: str) -> list[str]:
    body = mask_invisible_markdown(body)
    return [
        _slugify(m.group(1).strip()) for line in body.splitlines() if (m := _HEADING_RE.match(line))
    ]


def _err(file: Path, code: str, message: str) -> Finding:
    return Finding(file=str(file), line=1, severity=Severity.ERROR, code=code, message=message)


def lint_file(path: Path, *, seen_ids: dict[str, Path]) -> Iterator[Finding]:
    """Validate a single file. Mutates `seen_ids` for cross-file duplicate detection."""
    content = read_text_safe(path)
    if content is None:
        yield _err(path, "frontmatter-unreadable", "could not read file")
        return

    fm, body = parse_frontmatter(content)
    if fm is None:
        yield _err(path, "frontmatter-missing", "missing YAML frontmatter")
        return

    for field in _REQUIRED_FIELDS:
        if field not in fm:
            yield _err(path, "frontmatter-missing-field", f"missing required field '{field}'")

    if "index" not in fm:
        yield _err(path, "frontmatter-missing-field", "missing 'index' array")
        return

    index = fm["index"]
    if not isinstance(index, list):
        yield _err(path, "frontmatter-invalid-index", "'index' must be an array")
        return

    file_id = fm.get("id", "")
    if file_id:
        if file_id in seen_ids:
            yield _err(
                path,
                "frontmatter-duplicate-id",
                f"duplicate id '{file_id}' (also in {seen_ids[file_id]})",
            )
        else:
            seen_ids[file_id] = path

    slugs = _h2_slugs(body)
    for i, entry in enumerate(index):
        if not isinstance(entry, dict):
            yield _err(path, "frontmatter-invalid-index-entry", f"index[{i}] is not a mapping")
            continue
        entry_map = cast(dict[str, object], entry)
        if "id" not in entry_map:
            yield _err(path, "frontmatter-index-missing-id", f"index[{i}] missing 'id'")
            continue
        entry_id = entry_map["id"]
        if entry_id and entry_id not in slugs:
            yield _err(
                path,
                "frontmatter-index-heading-missing",
                f"index[{i}].id '{entry_id}' has no matching ## heading",
            )


def _find_docs_trees(root: Path) -> Iterator[tuple[Path, list[Path]]]:
    for tree in discover(root).docs_trees:
        docs_dir = tree.path
        files = []
        for md in sorted(docs_dir.rglob("*.md")):
            relative_to_tree = md.relative_to(docs_dir)
            if md.name in ("AGENTS.md", "README.md"):
                continue
            if "docs" in relative_to_tree.parts[:-1]:
                continue
            if any(p in EXCLUDED_DIRS for p in md.relative_to(root).parts):
                continue
            files.append(md)
        yield docs_dir, files


def lint(root: Path) -> LintResult:
    root = root.resolve()
    findings: list[Finding] = []
    for _docs_dir, files in _find_docs_trees(root):
        seen_ids: dict[str, Path] = {}
        contents = {path: read_text_safe(path) for path in files}
        for path, content in contents.items():
            if content is None:
                findings.append(_err(path, "frontmatter-unreadable", "could not read file"))
        convention_exists = any(
            content is not None and bool(parse_frontmatter(content)[0])
            for content in contents.values()
        )
        if not convention_exists:
            continue
        for file in files:
            if contents[file] is not None:
                findings.extend(lint_file(file, seen_ids=seen_ids))
    return LintResult(target=str(root), findings=findings)
