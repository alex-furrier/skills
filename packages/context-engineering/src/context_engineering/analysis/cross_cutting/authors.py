"""Author-overlap signal — who ships across multiple modules?"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path

from ...domain.commit import Commit
from ...infra.git import git_log
from .buckets import infer, module_for_path


def activity_by_author(
    commits: Iterable[Commit], module_roots: list[str]
) -> dict[str, Counter]:
    """author → Counter{module_root: commits_touching_it}"""
    out: dict[str, Counter] = defaultdict(Counter)
    for commit in commits:
        touched = {m for f in commit.files if (m := module_for_path(f, module_roots))}
        for m in touched:
            out[commit.author][m] += 1
    return dict(out)


def cross_cutting_authors(
    activity: dict[str, Counter], *, min_modules: int = 2
) -> list[tuple[str, dict[str, int]]]:
    out = [
        (author, dict(counts))
        for author, counts in activity.items()
        if len(counts) >= min_modules
    ]
    out.sort(key=lambda x: sum(x[1].values()), reverse=True)
    return out


def discover_partner_modules(
    repo_root: Path, target_module: str, lookback_days: int
) -> dict[str, Counter]:
    """For authors of `target_module`, which *other* buckets do they ship to?"""
    target_authors: set[str] = set()
    author_commits: dict[str, list[list[str]]] = defaultdict(list)

    for commit in git_log(repo_root, since_days=lookback_days):
        author_commits[commit.author].append(list(commit.files))
        if commit.touches(target_module):
            target_authors.add(commit.author)

    partners: dict[str, Counter] = defaultdict(Counter)
    for author in target_authors:
        for files in author_commits[author]:
            for f in files:
                bucket = infer(f)
                if bucket and bucket != target_module:
                    partners[author][bucket] += 1
    return dict(partners)
