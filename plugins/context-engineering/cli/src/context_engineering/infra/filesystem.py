"""Shared filesystem helpers — excluded-dir set + safe text read.

Each checker/analyzer does its own specialized discovery walk (docs-only,
AGENTS.md + docs pairs, git-tracked files), so we don't try to provide a
one-size-fits-all walker. Consumers check `EXCLUDED_DIRS` directly.
"""

from __future__ import annotations

from pathlib import Path

EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", ".venv", "_archive", "archive", "node_modules", "__pycache__"}
)


def read_text_safe(path: Path) -> str | None:
    """Read text or return None on OSError/UnicodeDecodeError/missing."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
