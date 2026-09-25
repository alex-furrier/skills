"""Rank explicitly supplied session artifacts without assuming a local agent layout."""
from __future__ import annotations

from pathlib import Path
from time import time

from ..domain.result import AnalysisResult


def analyze(project_path: str, max_results: int = 20, sessions_dir: str | None = None) -> AnalysisResult:
    """Count matching JSONL text lines in a caller-configured directory only."""
    result = AnalysisResult(target=project_path)
    root = Path(sessions_dir).expanduser() if sessions_dir else None
    if root is None:
        result.data = {"state": "unavailable", "reason": "No session artifact directory was configured; continue without session evidence."}
        return result
    if not root.is_dir():
        result.data = {"state": "unavailable", "reason": "Configured session artifact directory does not exist."}
        return result

    target = Path(project_path).resolve()
    full_path = str(target)
    basename = target.name
    now = time()
    sessions = []
    for artifact in root.rglob("*.jsonl"):
        try:
            modified = artifact.stat().st_mtime
            with artifact.open(encoding="utf-8") as stream:
                count = sum(1 for line in stream if full_path in line or (basename and basename in line))
        except (OSError, UnicodeError):
            continue
        if not count:
            continue
        age = max(0.0, (now - modified) / 86400)
        weight = max(0.1, 1 - age / 33)
        sessions.append({
            "path": str(artifact),
            "match_count": count,
            "age_days": round(age, 1),
            "recency_weight": round(weight, 2),
            "score": round(count * weight, 2),
        })
    sessions.sort(key=lambda session: (-session["score"], session["path"]))
    result.data = {"state": "available", "sessions": sessions[:max_results]}
    return result
