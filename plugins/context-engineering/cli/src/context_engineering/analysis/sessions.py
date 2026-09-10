"""Optional session-artifact discovery with no assumed agent or home-directory layout."""
from __future__ import annotations
from pathlib import Path
from ..domain.result import AnalysisResult

def analyze(project_path: str, max_results: int = 20, sessions_dir: str | None = None) -> AnalysisResult:
    """Return explicit unavailable evidence unless the caller configures a directory.

    This portable fallback deliberately never searches a personal agent-history path.
    A caller may supply exported JSONL artifacts through a configured directory.
    """
    result=AnalysisResult(target=project_path)
    root=Path(sessions_dir).expanduser() if sessions_dir else None
    if root is None:
        result.data={"state":"unavailable", "reason":"No session artifact directory was configured; continue without session evidence."}
        return result
    if not root.is_dir():
        result.data={"state":"unavailable", "reason":"Configured session artifact directory does not exist."}
        return result
    target=str(Path(project_path).resolve())
    hits=[]
    for artifact in root.rglob("*.jsonl"):
        try: count=artifact.read_text(encoding="utf-8").count(target)
        except OSError: continue
        if count: hits.append((count,artifact))
    result.data={"state":"available", "sessions":[{"path":str(artifact),"mentions":count} for count, artifact in sorted(hits, reverse=True)[:max_results]]}
    return result
