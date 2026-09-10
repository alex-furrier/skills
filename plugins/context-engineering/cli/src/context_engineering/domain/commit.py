"""Commit — git-log row with exact-segment path matching."""

from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    sha: str
    author: str
    date: datetime.datetime
    files: tuple[str, ...]

    def touches(self, prefix: str) -> bool:
        """True if any file is exactly `prefix` or lives under `prefix/`."""
        needle = prefix.rstrip("/")
        return any(f == needle or f.startswith(needle + "/") for f in self.files)
