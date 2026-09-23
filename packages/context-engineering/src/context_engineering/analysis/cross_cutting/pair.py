"""Pair mode — coupling between N specified modules."""

from __future__ import annotations

from pathlib import Path

from ...domain.finding import Finding, Severity
from ...domain.result import AnalysisResult
from ...infra.git import git_log, git_root
from . import authors, co_change, imports


def _resolve_modules(
    module_paths: list[Path], repo: Path
) -> tuple[list[Path], list[str], list[Finding]]:
    """Drop paths outside `repo`, returning a warning Finding for each drop.

    Both sides are resolved (symlinks followed) so a repo root reported by
    `git rev-parse` with a symlink component matches the same physical path
    the user supplied — matching what discover mode does.
    """
    repo_resolved = repo.resolve()
    inside_paths: list[Path] = []
    inside_roots: list[str] = []
    warnings: list[Finding] = []
    for mp in module_paths:
        try:
            inside_roots.append(str(mp.resolve().relative_to(repo_resolved)))
            inside_paths.append(mp)
        except ValueError:
            warnings.append(
                Finding(
                    file=str(mp),
                    line=0,
                    severity=Severity.WARNING,
                    code="cross-cutting-path-outside-repo",
                    message=f"skipping {mp}: not under repo root {repo}",
                )
            )
    return inside_paths, inside_roots, warnings


def _repo_for_any_path(module_paths: list[Path]) -> Path | None:
    """Return the git root for the first path that is inside a repository."""
    for module_path in module_paths:
        repo = git_root(module_path)
        if repo is not None:
            return repo
    return None


def pair(
    module_paths: list[Path],
    *,
    lookback_days: int = 90,
    min_edge: int = 3,
    signals: frozenset[str] = frozenset({"imports", "co-change", "authors"}),
) -> AnalysisResult:
    if not module_paths:
        return AnalysisResult(
            target="<not-a-repo>", data={"error": "no module paths provided", "mode": "pair"}
        )

    repo = _repo_for_any_path(module_paths)
    if repo is None:
        return AnalysisResult(
            target="<not-a-repo>", data={"error": "not in a git repo", "mode": "pair"}
        )

    resolved_paths, module_roots, findings = _resolve_modules(module_paths, repo)

    data: dict = {
        "repo_root": str(repo),
        "modules": module_roots,
        "lookback_days": lookback_days,
        "mode": "pair",
    }

    if "imports" in signals:
        edges = imports.edges_between(resolved_paths, module_roots)
        data["import_edges"] = {
            src: [
                {"target": t, "count": c}
                # -count primary, name secondary → stable ordering.
                # Apply min_edge consistently — discover mode filters all
                # three signals, and pair's co-change does too.
                for t, c in sorted(cs.items(), key=lambda x: (-x[1], x[0]))
                if c >= min_edge
            ]
            for src, cs in edges.items()
        }

    # Share the history walk: co-change wants commits that touch a module
    # root; authors wants the full stream. Pull once, slice twice.
    if {"co-change", "authors"} & signals:
        all_commits = list(git_log(repo, since_days=lookback_days))

        if "co-change" in signals:
            touching = [
                c for c in all_commits
                if any(c.touches(r) for r in module_roots)
            ]
            pairs = co_change.pairs_between(touching, module_roots)
            data["co_change_pairs"] = [
                {"modules": list(p), "commits": c}
                for p, c in sorted(pairs.items(), key=lambda x: (-x[1], x[0]))
                if c >= min_edge
            ]
            data["co_change_total_commits"] = len(touching)

        if "authors" in signals:
            activity = authors.activity_by_author(all_commits, module_roots)
            data["cross_cutting_authors"] = [
                {"author": a, "modules": m}
                for a, m in authors.cross_cutting_authors(activity, min_modules=2)
            ]

    return AnalysisResult(target=str(module_paths[0]), data=data, findings=findings)
