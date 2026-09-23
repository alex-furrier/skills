"""Static-import signal — collect Python imports, count cross-module edges."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .buckets import infer, module_for_path

_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([a-zA-Z0-9_.]+)\s+import\b|import\s+([a-zA-Z0-9_.]+))",
    re.MULTILINE,
)


def collect(module_path: Path) -> set[str]:
    """Every dotted import path referenced from Python files under `module_path`."""
    imports: set[str] = set()
    for py in module_path.rglob("*.py"):
        try:
            content = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in _IMPORT_RE.finditer(content):
            name = match.group(1) or match.group(2)
            if name:
                imports.add(name)
    return imports


def edges_between(
    module_paths: list[Path], module_roots: list[str]
) -> dict[str, Counter]:
    """For each source module, count imports that resolve into a *different* input module."""
    result: dict[str, Counter] = {root: Counter() for root in module_roots}
    for src_path, src_root in zip(module_paths, module_roots, strict=True):
        for imp in collect(src_path):
            imp_path = imp.replace(".", "/")
            target = module_for_path(imp_path, module_roots)
            if target and target != src_root:
                result[src_root][target] += 1
    return result


def discover_targets(module_path: Path, repo_root: Path) -> Counter:
    """Count buckets the input imports from (for discover mode)."""
    try:
        src_bucket = infer(str(module_path.relative_to(repo_root)))
    except ValueError:
        src_bucket = None

    counts: Counter = Counter()
    for imp in collect(module_path):
        bucket = infer(imp.replace(".", "/"))
        if bucket is None or bucket == src_bucket:
            continue
        if not (repo_root / bucket).exists():
            continue
        counts[bucket] += 1
    return counts
