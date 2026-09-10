"""Git co-change signal — count file pairs touched in the same commit."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from ...domain.commit import Commit
from ...infra.git import git_log
from .buckets import infer, module_for_path


def pairs_between(commits: Iterable[Commit], module_roots: list[str]) -> Counter:
    """Count how often each pair of `module_roots` co-changes."""
    pairs: Counter = Counter()
    for commit in commits:
        touched = {
            m for f in commit.files if (m := module_for_path(f, module_roots))
        }
        ordered = sorted(touched)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                pairs[(ordered[i], ordered[j])] += 1
    return pairs


def discover_partners(
    repo_root: Path, target_module: str, lookback_days: int
) -> tuple[Counter, int]:
    """(partners, total_commits_touching_target) — `discover` mode counterpart."""
    partners: Counter = Counter()
    total = 0
    for commit in git_log(repo_root, since_days=lookback_days):
        if not commit.touches(target_module):
            continue
        total += 1
        others: set[str] = set()
        for f in commit.files:
            if f == target_module or f.startswith(target_module + "/"):
                continue
            bucket = infer(f)
            if bucket and bucket != target_module:
                others.add(bucket)
        for bucket in others:
            partners[bucket] += 1
    return partners, total
