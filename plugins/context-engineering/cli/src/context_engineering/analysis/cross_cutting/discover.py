"""Discover mode — auto-find partners of a single target module."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ...domain.result import AnalysisResult
from ...infra.git import git_root
from . import authors, co_change, imports


def _rank(counts: Counter, *, top_n: int, min_edge: int = 0) -> list[tuple[str, int]]:
    """Stable ranking by (-count, name) so tie-breaking is deterministic."""
    return sorted(
        ((k, v) for k, v in counts.items() if v >= min_edge),
        key=lambda x: (-x[1], x[0]),
    )[:top_n]


def discover(
    target_path: Path,
    *,
    lookback_days: int = 90,
    min_edge: int = 3,
    top_n: int = 10,
    signals: frozenset[str] = frozenset({"imports", "co-change", "authors"}),
) -> AnalysisResult:
    repo = git_root(target_path)
    if repo is None:
        return AnalysisResult(
            target=str(target_path),
            data={"error": "not in a git repo", "mode": "discover"},
        )

    try:
        target_rel = str(target_path.resolve().relative_to(repo.resolve()))
    except ValueError:
        target_rel = str(target_path)

    data: dict = {
        "repo_root": str(repo),
        "modules": [target_rel],
        "lookback_days": lookback_days,
        "mode": "discover",
    }

    if "imports" in signals:
        import_counts = imports.discover_targets(target_path, repo)
        data["discovered_imports"] = [
            {"module": m, "count": c}
            for m, c in _rank(import_counts, top_n=top_n, min_edge=min_edge)
        ]

    if "co-change" in signals:
        partners, total = co_change.discover_partners(repo, target_rel, lookback_days)
        data["discovered_co_change"] = [
            {"module": m, "shared_commits": c}
            for m, c in _rank(partners, top_n=top_n, min_edge=min_edge)
        ]
        data["co_change_total_commits_touching_target"] = total

    if "authors" in signals:
        author_partners = authors.discover_partner_modules(repo, target_rel, lookback_days)
        module_to_authors: Counter = Counter()
        for counts in author_partners.values():
            for m in counts:
                module_to_authors[m] += 1
        data["discovered_by_authors"] = [
            {"module": m, "shared_authors": c}
            for m, c in _rank(module_to_authors, top_n=top_n, min_edge=min_edge)
        ]
        data["target_author_count"] = len(author_partners)

    return AnalysisResult(target=target_rel, data=data)
