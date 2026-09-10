"""Context passed to each checker — depth, modified flag, shared git metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckContext:
    root: Path
    git_root: Path | None
    modified_only: bool

    def depth(self, path: Path) -> int:
        """Depth of `path.parent` relative to git root. Falls back to 2 (leaf default)."""
        if self.git_root is None:
            return 2
        try:
            rel = path.parent.resolve().relative_to(self.git_root.resolve())
            return len([p for p in rel.parts if p != "."])
        except ValueError:
            return 2
