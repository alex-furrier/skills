"""Recommend whether an AGENTS.md needs refreshing based on recent git activity."""

from __future__ import annotations

import datetime
from pathlib import Path

from ..domain.result import AnalysisResult
from ..infra.git import git_log, git_root
from .impact import Impact, classify_with_reason


def _last_update(agents_path: Path) -> tuple[str, str]:
    """(sha, iso_date) of the most recent commit that touched `agents_path`."""
    repo = git_root(agents_path.parent)
    if repo is None:
        return "", ""
    # `git log -- <path>` pathspecs are repo-relative, and git_log runs from
    # the repo root. Pass the full repo-relative path so nested AGENTS.md
    # files (e.g. services/payments/AGENTS.md) actually match their history.
    try:
        rel = str(agents_path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return "", ""
    commit = next(git_log(repo, paths=[rel], max_count=1), None)
    if commit is None:
        return "", ""
    return commit.sha, commit.date.isoformat()


def _days_since(iso_date: str) -> int:
    if not iso_date:
        return 0
    try:
        dt = datetime.datetime.fromisoformat(iso_date)
    except ValueError:
        return -1
    return (datetime.datetime.now(datetime.UTC) - dt).days


def recommend(*, commits_since: int, high: int, medium: int, days_since: int) -> str:
    if commits_since == 0:
        return "skip"
    if days_since > 30 or commits_since > 50:
        return "full-rebuild"
    if high > 0:
        return "full-update"
    if medium > 0:
        return "partial-update"
    return "skip"


def _recommendation_reasons(
    *, commits_since: int, high: int, medium: int, days_since: int
) -> list[str]:
    if commits_since == 0:
        return ["no commits touched the scoped module since the AGENTS.md update"]
    if days_since > 30 or commits_since > 50:
        reasons = []
        if days_since > 30:
            reasons.append(f"{days_since} days exceeds the 30-day rebuild threshold")
        if commits_since > 50:
            reasons.append(
                f"{commits_since} commits exceeds the 50-commit rebuild threshold"
            )
        return reasons
    if high > 0:
        return [f"{high} changed paths matched high-impact rules"]
    if medium > 0:
        return [f"{medium} changed paths classified medium impact"]
    return ["all changed paths defaulted to low impact"]


def analyze(agents_path: Path) -> AnalysisResult:
    agents_path = agents_path.resolve()

    if not agents_path.exists():
        return AnalysisResult(
            target=str(agents_path),
            data={
                "recommendation": "full-rebuild",
                "recommendation_advisory": True,
                "recommendation_reasons": ["the target AGENTS.md does not exist"],
                "changed_files": [],
                "error": f"{agents_path} not found",
            },
        )

    repo = git_root(agents_path)
    if repo is None:
        return AnalysisResult(
            target=str(agents_path),
            data={
                "recommendation": "full-rebuild",
                "recommendation_advisory": True,
                "recommendation_reasons": ["the target is not in a git repository"],
                "changed_files": [],
                "error": "Not a git repository",
            },
        )

    last_sha, last_date = _last_update(agents_path)

    # Scope the scan to the module directory — for a nested AGENTS.md like
    # `services/payments/AGENTS.md`, we only care about commits that touched
    # `services/payments/`. Walking the entire repo inflates commit counts and
    # counts unrelated Dockerfiles/CI configs as HIGH-impact, which made
    # the recommendation default to "full-rebuild" for every non-root
    # AGENTS.md in a busy monorepo.
    try:
        scope = str(agents_path.parent.resolve().relative_to(repo.resolve()))
    except ValueError:
        scope = "."
    scope_paths = [scope] if scope and scope != "." else None

    commits_iter = (
        git_log(repo, since_ref=last_sha, paths=scope_paths)
        if last_sha
        else git_log(repo, paths=scope_paths)
    )
    commits = 0
    files: set[str] = set()
    for commit in commits_iter:
        commits += 1
        files.update(commit.files)

    changed_files: list[dict[str, str]] = []
    impact_counts = {impact: 0 for impact in Impact}
    for f in sorted(files):
        classification = classify_with_reason(f)
        impact_counts[classification.impact] += 1
        changed_files.append(
            {
                "path": f,
                "impact": classification.impact.value,
                "classification_reason": classification.reason,
            }
        )

    days_since = _days_since(last_date)
    # A never-committed AGENTS.md (`last_sha == ""`) is not "fresh" — it's
    # untracked. Force full-rebuild instead of letting days_since=0 trick the
    # heuristic into "skip".
    if not last_sha:
        rec = "full-rebuild"
    else:
        rec = recommend(
            commits_since=commits,
            high=impact_counts[Impact.HIGH],
            medium=impact_counts[Impact.MEDIUM],
            days_since=days_since,
        )

    if not last_sha:
        recommendation_reasons = ["the AGENTS.md has no committed update"]
    else:
        recommendation_reasons = _recommendation_reasons(
            commits_since=commits,
            high=impact_counts[Impact.HIGH],
            medium=impact_counts[Impact.MEDIUM],
            days_since=days_since,
        )

    return AnalysisResult(
        target=str(agents_path),
        data={
            "agents_file": str(agents_path),
            "last_updated": {"commit": last_sha, "date": last_date},
            "commits_since": commits,
            "days_since": days_since,
            "changed_files": changed_files,
            "impact_summary": {
                impact.value: impact_counts[impact] for impact in Impact
            },
            "recommendation": rec,
            "recommendation_advisory": True,
            "recommendation_reasons": recommendation_reasons,
        },
    )
