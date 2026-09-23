"""Validate skill directory layout."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ..domain.finding import Finding, Severity
from ..domain.result import LintResult
from ..infra.filesystem import read_text_safe
from ..infra.yaml_frontmatter import parse_frontmatter

_EXPECTED_SUBDIRS = frozenset({"scripts", "references", "resources", "assets"})
_ALLOWED_TOP_LEVEL = frozenset({"SKILL.md", "SYNC.md", "README.md"})
_SOFT_LINE_LIMIT = 500


def _finding(path: Path, code: str, message: str, severity: Severity = Severity.ERROR) -> Finding:
    return Finding(file=str(path), line=0, severity=severity, code=code, message=message)


def lint_skill(skill_dir: Path) -> Iterator[Finding]:
    if not skill_dir.is_dir():
        yield _finding(skill_dir, "skill-not-a-directory", f"{skill_dir} is not a directory")
        return

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        yield _finding(skill_dir, "skill-missing-skill-md", "SKILL.md not found")
        return

    content = read_text_safe(skill_md) or ""
    fm, _ = parse_frontmatter(content)

    if fm is None:
        yield _finding(skill_md, "skill-no-frontmatter", "SKILL.md has no YAML frontmatter")
    else:
        if "name" not in fm:
            yield _finding(skill_md, "skill-missing-name", "frontmatter missing 'name'")
        if "description" not in fm:
            yield _finding(
                skill_md,
                "skill-missing-description",
                "frontmatter missing 'description'",
            )
        if "name" in fm and fm["name"] != skill_dir.name:
            yield _finding(
                skill_md,
                "skill-name-mismatch",
                f"frontmatter name '{fm['name']}' differs from directory '{skill_dir.name}'",
                Severity.WARNING,
            )

    line_count = len(content.splitlines())
    if line_count > _SOFT_LINE_LIMIT:
        yield _finding(
            skill_md,
            "skill-oversized",
            f"SKILL.md is {line_count} lines (target <{_SOFT_LINE_LIMIT})",
            Severity.WARNING,
        )

    yield from _lint_layout(skill_dir)
    yield from _lint_scripts(skill_dir)
    yield from _lint_references(skill_dir)


def _lint_layout(skill_dir: Path) -> Iterator[Finding]:
    for item in sorted(skill_dir.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_dir() and item.name not in _EXPECTED_SUBDIRS:
            yield _finding(
                item,
                "skill-unexpected-subdir",
                f"unexpected subdirectory: {item.name}/",
                Severity.WARNING,
            )
        elif item.is_file() and item.name not in _ALLOWED_TOP_LEVEL:
            yield _finding(
                item,
                "skill-unexpected-top-level-file",
                f"unexpected top-level file: {item.name}",
                Severity.WARNING,
            )


def _lint_scripts(skill_dir: Path) -> Iterator[Finding]:
    scripts = skill_dir / "scripts"
    if not scripts.is_dir():
        return
    for py in sorted(scripts.glob("*.py")):
        source = read_text_safe(py)
        if source is None:
            yield _finding(py, "skill-unreadable-script", "could not read script")
            continue
        # `compile()` does a pure syntax/parse check — no __pycache__ side
        # effects like py_compile. A lint should be read-only.
        try:
            compile(source, str(py), "exec")
        except SyntaxError as e:
            yield _finding(py, "skill-script-compile-error", f"compile error: {e}")


def _lint_references(skill_dir: Path) -> Iterator[Finding]:
    for sub in ("references", "resources"):
        subdir = skill_dir / sub
        if not subdir.is_dir():
            continue
        for md in sorted(subdir.glob("*.md")):
            if read_text_safe(md) is None:
                yield _finding(md, "skill-unreadable-file", f"unreadable {sub} file")


def lint(target: Path, *, recurse: bool = False) -> LintResult:
    """If `recurse`, treat `target` as a parent of skills; otherwise target is one skill."""
    if not recurse:
        return LintResult(target=str(target), findings=list(lint_skill(target)))

    findings: list[Finding] = []
    for skill in sorted(target.iterdir()):
        if skill.is_dir() and (skill / "SKILL.md").exists():
            findings.extend(lint_skill(skill))
    return LintResult(target=str(target), findings=findings)
