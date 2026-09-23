"""Inspect a Git diff without turning semantic routing hints into authority."""

from __future__ import annotations

from pathlib import Path

from ..domain.finding import Finding, Severity
from ..domain.result import AnalysisResult
from ..infra.git import git_root, resolve_commit, resolve_merge_base
from ..infra.git_evidence import read_diff

_STATUS = {
    "A": "added",
    "C": "copied",
    "D": "deleted",
    "M": "modified",
    "R": "renamed",
    "T": "type-changed",
}


def _diff(
    repo: Path,
    module: Path,
    base: str,
    head: str,
) -> tuple[list[dict[str, str]], str | None]:
    relative = module.relative_to(repo).as_posix()
    changes, error = read_diff(repo, base=base, head=head)
    if error:
        return [], error
    changed: list[dict[str, str]] = []
    for change in changes:
        raw_status = change.status
        code = raw_status[:1]
        entry = {"status": _STATUS.get(code, raw_status.casefold()), "path": change.path}
        if change.old_path is not None:
            entry["old_path"] = change.old_path
        paths = [entry["path"], *([entry["old_path"]] if "old_path" in entry else [])]
        in_scope = relative == "." or any(
            path == relative or path.startswith(f"{relative}/") for path in paths
        )
        if not in_scope:
            continue
        if relative != ".":
            for key in ("path", "old_path"):
                if key in entry and entry[key].startswith(f"{relative}/"):
                    entry[key] = entry[key][len(relative) + 1 :]
        changed.append(entry)
    return sorted(changed, key=lambda item: (item["path"], item["status"])), None


def _route(path: str) -> list[tuple[str, str]]:
    lowered = path.casefold()
    routes: list[tuple[str, str]] = []
    if Path(lowered).name == "spec.md":
        routes.append(("SPEC.md", "the diff directly changes the current contract"))
    has_adr_path = any(part in lowered for part in ("/adr/", "/adrs/", "/decisions/"))
    if has_adr_path or lowered.startswith(("adr/", "adrs/")):
        routes.append(("ADR", "the diff directly changes a decision record"))
    if lowered.endswith("agents.md"):
        routes.append(("AGENTS.md", "the diff changes agent routing or repository gotchas"))
    if lowered.endswith("skill.md") or "/skills/" in lowered or lowered.startswith("skills/"):
        routes.append(("skill", "the diff changes a repeatable agent workflow"))
    has_doc_path = "/reference/" in lowered or "/explanation/" in lowered
    if has_doc_path or lowered.startswith(("docs/reference/", "docs/explanation/")):
        routes.append(
            (
                "architecture/reference docs",
                "the diff changes durable explanatory or lookup context",
            )
        )
    source_suffixes = {
        ".bash",
        ".c",
        ".cc",
        ".cjs",
        ".cpp",
        ".cs",
        ".cxx",
        ".dart",
        ".ex",
        ".exs",
        ".fish",
        ".go",
        ".h",
        ".hcl",
        ".hpp",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".kt",
        ".kts",
        ".lua",
        ".mjs",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".sql",
        ".svelte",
        ".swift",
        ".tf",
        ".toml",
        ".ts",
        ".tsx",
        ".vue",
        ".xml",
        ".yaml",
        ".yml",
        ".zsh",
    }
    if not routes and Path(lowered).suffix in source_suffixes:
        routes.extend(
            (
                (
                    "SPEC.md",
                    "implementation or configuration changed; inspect whether current "
                    "behavior or invariants moved",
                ),
                (
                    "ADR",
                    "implementation or configuration changed; inspect whether a lasting "
                    "decision was introduced",
                ),
            )
        )
    if not routes:
        routes.append(("no update", "no deterministic context owner follows from the path alone"))
    return routes


def analyze(module: Path, *, base: str, head: str = "HEAD") -> AnalysisResult:
    module = module.resolve()
    repo = git_root(module)
    if repo is None:
        finding = Finding(
            str(module),
            0,
            Severity.ERROR,
            "context-review-not-git",
            "Target is not in a Git repository",
        )
        return AnalysisResult(
            target=str(module),
            data={
                "range": {"base": base, "head": head},
                "changed_paths": [],
                "evidence": [],
                "advisory_routes": [],
                "deterministic_errors": [
                    {"code": "not-a-git-repository", "message": finding.message}
                ],
                "write_performed": False,
            },
            findings=[finding],
        )
    resolved_base, base_error = resolve_commit(repo, base)
    resolved_head, head_error = resolve_commit(repo, head)
    findings: list[Finding] = []
    deterministic_errors: list[dict[str, str]] = []
    merge_base: str | None = None
    error = base_error or head_error
    if error is None:
        assert resolved_base is not None and resolved_head is not None
        merge_base, error = resolve_merge_base(repo, resolved_base, resolved_head)
    changed: list[dict[str, str]] = []
    if error is None:
        assert resolved_base is not None and resolved_head is not None
        changed, error = _diff(repo, module, resolved_base, resolved_head)
    if error:
        deterministic_errors.append({"code": "invalid-git-range", "message": error})
        findings.append(
            Finding(str(module), 0, Severity.ERROR, "context-review-invalid-range", error)
        )
    exact_base = resolved_base or base
    exact_head = resolved_head or head
    evidence = [
        {**entry, "source": "git-diff", "range": f"{exact_base}...{exact_head}"}
        for entry in changed
    ]
    advisory_routes: list[dict[str, object]] = []
    for index, entry in enumerate(changed):
        route_reasons: dict[str, str] = {}
        route_paths: dict[str, list[str]] = {}
        paths = [entry["path"]]
        if "old_path" in entry:
            paths.append(entry["old_path"])
        for path in paths:
            for route, reason in _route(path):
                route_reasons.setdefault(route, reason)
                route_paths.setdefault(route, []).append(path)
        for route, reason in route_reasons.items():
            advisory_routes.append(
                {
                    "path": entry["path"],
                    "paths": route_paths[route],
                    "route": route,
                    "reason": reason,
                    "authority": "advisory",
                    "evidence_index": index,
                }
            )
    return AnalysisResult(
        target=str(module),
        data={
            "range": {
                "base": exact_base,
                "head": exact_head,
                "merge_base": merge_base,
                "requested_base": base,
                "requested_head": head,
            },
            "changed_paths": changed,
            "evidence": evidence,
            "advisory_routes": advisory_routes,
            "deterministic_errors": deterministic_errors,
            "write_performed": False,
        },
        findings=findings,
    )
