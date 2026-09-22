"""Infer a module bucket from a repo-relative file path.

Used by discover mode to answer "what bucket does this file belong to?" The
patterns below cover common monorepo layouts. Anything else falls back to the
top-level directory.
"""

from __future__ import annotations

# Common generic monorepo containers. For paths under these directories, use the
# next segment as the module name: `services/billing/api.py` -> `services/billing`.
_PATTERNS: tuple[tuple[str, ...], ...] = (
    ("apps",),
    ("packages",),
    ("services",),
    ("libs",),
    ("plugins",),
    ("tools",),
)


def infer(path: str) -> str | None:
    """Return the enclosing module bucket for `path`, or None for top-level files."""
    parts = path.split("/")
    if len(parts) < 2:
        return None
    for pattern in _PATTERNS:
        if len(parts) > len(pattern) and tuple(parts[: len(pattern)]) == pattern:
            return "/".join(parts[: len(pattern) + 1])
    return parts[0]


def module_for_path(rel_path: str, module_roots: list[str]) -> str | None:
    """Match `rel_path` to the longest prefix in `module_roots`, or None."""
    best: str | None = None
    for root in module_roots:
        if rel_path == root or rel_path.startswith(root.rstrip("/") + "/"):
            if best is None or len(root) > len(best):
                best = root
    return best
