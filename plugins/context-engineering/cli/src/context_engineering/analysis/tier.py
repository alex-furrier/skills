"""Classify a module's opinion-density tier from its recent unique authors."""

from __future__ import annotations

from pathlib import Path

from ..domain.result import AnalysisResult
from ..infra.git import git_log, git_root

_TIERS: tuple[tuple[int, str], ...] = (
    (0, "unknown"),
    (1, "1"),
    (5, "2-5"),
    (20, "6-20"),
)


def classify(unique_authors: int) -> str:
    for threshold, label in _TIERS:
        if unique_authors <= threshold:
            return label
    return "21+"


_GUIDANCE: dict[str, dict[str, str]] = {
    "unknown": {
        "multi_path_commands": (
            "No history in lookback window — default to listing options neutrally; "
            "be conservative"
        ),
        "how_to_work_here": (
            "No tier signal — skip unless code structure makes a canonical flow obvious"
        ),
        "gotcha_budget_default": "5-7",
    },
    "1": {
        "multi_path_commands": "Pick the canonical path; one contributor owns it",
        "how_to_work_here": "Opinionated step-by-step is appropriate",
        "gotcha_budget_default": "7",
    },
    "2-5": {
        "multi_path_commands": "Pick a default with a one-line rationale",
        "how_to_work_here": "Opinionated, validated by the small team",
        "gotcha_budget_default": "7",
    },
    "6-20": {
        "multi_path_commands": "List options with tradeoff notes; don't prescribe a default",
        "how_to_work_here": "Brief pointer to canonical flow",
        "gotcha_budget_default": "7",
    },
    "21+": {
        "multi_path_commands": "List options neutrally or defer to --help / nested AGENTS.md",
        "how_to_work_here": "Drop; candidates go to SKIPPED_FOR_REVIEW.md",
        "gotcha_budget_default": "5-7",
    },
}


def guidance(tier: str) -> dict[str, str]:
    return dict(_GUIDANCE[tier])


def analyze(module_path: Path, *, lookback_days: int = 90) -> AnalysisResult:
    repo = git_root(module_path)
    try:
        target = (
            str(module_path.resolve().relative_to(repo.resolve()))
            if repo
            else str(module_path)
        )
    except ValueError:
        target = str(module_path)

    authors: set[str] = set()
    total = 0
    for commit in git_log(module_path, since_days=lookback_days, paths=[target]):
        authors.add(commit.author)
        total += 1

    tier = classify(len(authors))
    return AnalysisResult(
        target=target,
        data={
            "path": target,
            "lookback_days": lookback_days,
            "unique_authors": len(authors),
            "total_commits": total,
            "tier": tier,
            "guidance": guidance(tier),
        },
    )
