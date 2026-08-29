"""Compose deterministic contract checks with advisory diff review."""

from __future__ import annotations

from pathlib import Path

from ..checks import contracts, frontmatter, references, skill_structure
from ..domain.finding import Finding, Severity
from ..domain.result import AnalysisResult
from ..infra.git import git_root
from ..infra.git_tree import materialize_tree
from . import context_review
from .context_layout import RepositoryContextLayout, discover, is_ignored_contract_path


def _relative_owners(layout: RepositoryContextLayout) -> tuple[Path, ...]:
    roots = {
        *(path.parent for path in layout.specs),
        *(tree.path.parent for tree in layout.adr_trees),
        *(tree.path for tree in layout.docs_trees),
        *(path.parent for path in layout.agents_files),
        *(tree for tree in layout.skill_roots),
    }
    relative = (path.relative_to(layout.root) for path in roots)
    return tuple(sorted(relative, key=lambda path: path.as_posix()))


def _affected_roots(
    owners: tuple[Path, ...], changed: list[dict[str, str]], *, all_context: bool
) -> tuple[Path, ...]:
    if all_context:
        return owners
    affected: set[Path] = set()
    for entry in changed:
        for raw_path in (entry.get("path"), entry.get("old_path")):
            if raw_path is None:
                continue
            path = Path(raw_path)
            matches = [root for root in owners if path == root or root in path.parents]
            if matches:
                affected.add(max(matches, key=lambda root: len(root.parts)))
    return tuple(sorted(affected, key=lambda path: path.as_posix()))


def _deleted_contract_path(entry: dict[str, str]) -> bool:
    """Return whether a changed path removes a non-template SPEC contract."""
    path = Path(entry["path"])
    if entry.get("status") == "deleted":
        return path.name == "SPEC.md" and not is_ignored_contract_path(path)
    if entry.get("status") == "renamed":
        old_path = Path(entry.get("old_path", ""))
        return (
            old_path.name == "SPEC.md"
            and not is_ignored_contract_path(old_path)
            and path.name != "SPEC.md"
        )
    return False


def _finding_in_roots(finding: Finding, tree: Path, roots: tuple[Path, ...]) -> bool:
    if not roots:
        return False
    path = Path(finding.file)
    if path.is_absolute():
        try:
            relative = path.resolve().relative_to(tree.resolve())
        except ValueError:
            return False
    else:
        relative = path
    return any(relative == root or root in relative.parents for root in roots)


def _normalized_finding(finding: Finding, module: Path) -> Finding:
    path = Path(finding.file)
    if path.is_absolute():
        try:
            file = path.resolve().relative_to(module.resolve()).as_posix()
        except ValueError:
            file = finding.file
    else:
        file = finding.file
    return Finding(
        file=file,
        line=finding.line,
        severity=finding.severity,
        code=finding.code,
        message=finding.message.replace(str(module), "."),
        hint=finding.hint,
    )


def _validate(module: Path) -> list[Finding]:
    findings = [
        *contracts.analyze(module).findings,
        *frontmatter.lint(module).findings,
        *references.lint(module).findings,
    ]
    for skill_root in discover(module).skill_roots:
        findings.extend(skill_structure.lint(skill_root, recurse=True).findings)
    return findings


def analyze(
    module: Path,
    *,
    base: str,
    head: str = "HEAD",
    all_context: bool = False,
) -> AnalysisResult:
    """Run one read-only PR-time journey with deterministic and advisory outputs."""
    module = module.resolve()
    review = context_review.analyze(module, base=base, head=head)
    repo = git_root(module)
    if repo is None or review.has_errors:
        return AnalysisResult(
            target=str(module),
            data={**review.data, "affected_context_roots": [], "deterministic_findings": []},
            findings=review.findings,
        )
    relative_module = module.relative_to(repo)
    exact_base = str(review.data["range"]["merge_base"])
    exact_head = str(review.data["range"]["head"])
    findings: list[Finding] = [
        Finding(
            entry["path"],
            0,
            Severity.ERROR,
            "context-check-contract-deleted",
            "A SPEC.md contract was deleted in this range",
        )
        for entry in review.data["changed_paths"]
        if _deleted_contract_path(entry)
    ]
    affected: tuple[Path, ...] = ()
    with materialize_tree(repo, exact_base) as (base_tree, base_error):
        if base_error is not None or base_tree is None:
            findings.append(
                Finding(
                    str(module),
                    0,
                    Severity.ERROR,
                    "context-check-tree-unavailable",
                    base_error or "base tree is unavailable",
                )
            )
        with materialize_tree(repo, exact_head) as (head_tree, head_error):
            if head_error is not None or head_tree is None:
                findings.append(
                    Finding(
                        str(module),
                        0,
                        Severity.ERROR,
                        "context-check-tree-unavailable",
                        head_error or "head tree is unavailable",
                    )
                )
            else:
                head_module = (head_tree / relative_module).resolve()
                base_module = (
                    (base_tree / relative_module).resolve() if base_tree is not None else None
                )
                if not head_module.is_dir():
                    findings.append(
                        Finding(
                            str(relative_module),
                            0,
                            Severity.ERROR,
                            "context-check-target-deleted",
                            "The target module does not exist in the head tree",
                        )
                    )
                head_layout = discover(head_module) if head_module.is_dir() else None
                base_layout = (
                    discover(base_module)
                    if base_module is not None and base_module.is_dir()
                    else None
                )
                head_owners = _relative_owners(head_layout) if head_layout is not None else ()
                base_owners = _relative_owners(base_layout) if base_layout is not None else ()
                owners = tuple(
                    sorted(set((*head_owners, *base_owners)), key=lambda path: path.as_posix())
                )
                affected = _affected_roots(
                    owners,
                    list(review.data["changed_paths"]),
                    all_context=all_context,
                )
                changed_endpoints = {
                    path
                    for entry in review.data["changed_paths"]
                    for path in (entry.get("path"), entry.get("old_path"))
                    if path is not None
                }
                if base_layout is not None:
                    base_specs = {
                        path.relative_to(base_layout.root).as_posix() for path in base_layout.specs
                    }
                    head_specs = (
                        {
                            path.relative_to(head_layout.root).as_posix()
                            for path in head_layout.specs
                        }
                        if head_layout is not None
                        else set()
                    )
                    findings.extend(
                        Finding(
                            path,
                            0,
                            Severity.ERROR,
                            "context-check-contract-deleted",
                            "A SPEC.md contract was removed from this context owner",
                        )
                        for path in sorted(base_specs - head_specs)
                        if path in changed_endpoints
                    )
                if head_module.is_dir():
                    head_candidates = [
                        _normalized_finding(item, head_module) for item in _validate(head_module)
                    ]
                    if all_context:
                        findings.extend(head_candidates)
                    else:
                        head_candidates = [
                            item
                            for item in head_candidates
                            if _finding_in_roots(item, head_module, affected)
                        ]
                        base_candidates: set[Finding] = set()
                        if base_module is not None and base_module.is_dir():
                            base_candidates = {
                                _normalized_finding(item, base_module)
                                for item in _validate(base_module)
                                if _finding_in_roots(item, base_module, affected)
                            }
                        findings.extend(
                            item for item in head_candidates if item not in base_candidates
                        )
    findings = sorted(set(findings))
    return AnalysisResult(
        target=str(module),
        data={
            "range": review.data["range"],
            "changed_paths": review.data["changed_paths"],
            "affected_context_roots": [path.as_posix() or "." for path in affected],
            "deterministic_findings": [finding.to_dict() for finding in findings],
            "advisory_routes": review.data["advisory_routes"],
            "write_performed": False,
        },
        findings=findings,
    )
