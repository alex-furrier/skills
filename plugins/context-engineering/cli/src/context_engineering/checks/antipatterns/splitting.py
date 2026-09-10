"""P3: splitting-candidate — 3+ gotcha bullets clustering under a common path.

Signal that the AGENTS.md wants to be split — promote a nested
<subdir>/AGENTS.md rather than pack more into the current one.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from ...domain.finding import Finding, Severity
from ...infra.filesystem import read_text_safe
from .context import CheckContext

_FILEREF_RE = re.compile(r"`([a-zA-Z0-9_./\-]+\.[a-zA-Z0-9_]+)(?::\d+(?:-\d+)?)?`")
_MIN_BULLETS = 3


def _parse_bullets(content: str) -> list[list[str]]:
    """Return one list of referenced paths per DO bullet."""
    bullets: list[list[str]] = []
    current: list[str] = []
    in_bullet = False

    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("- **DO**"):
            if in_bullet and current:
                bullets.append(current)
            current = []
            in_bullet = True
        elif not stripped and in_bullet:
            if current:
                bullets.append(current)
            current = []
            in_bullet = False

        if in_bullet:
            for m in _FILEREF_RE.finditer(line):
                ref = m.group(1)
                if "/" in ref:
                    current.append(ref)

    if in_bullet and current:
        bullets.append(current)
    return bullets


def _count_prefixes(bullets: list[list[str]]) -> tuple[Counter, dict[str, list[str]]]:
    prefix_bullets: Counter = Counter()
    samples: dict[str, list[str]] = {}
    for paths in bullets:
        prefixes: set[str] = set()
        for p in paths:
            parts = p.split("/")
            for n in (1, 2, 3):
                if len(parts) > n:
                    prefixes.add("/".join(parts[:n]))
        for prefix in prefixes:
            prefix_bullets[prefix] += 1
            samples.setdefault(prefix, []).extend(paths)
    return prefix_bullets, samples


def check(path: Path, _ctx: CheckContext) -> Iterator[Finding]:
    if path.name not in ("AGENTS.md", "CLAUDE.md"):
        return
    content = read_text_safe(path)
    if content is None:
        return

    bullets = _parse_bullets(content)
    prefix_bullets, samples = _count_prefixes(bullets)

    for prefix, count in prefix_bullets.most_common():
        if count < _MIN_BULLETS:
            break
        # Exact-segment match: `chat_bot` as file parent should NOT suppress
        # a warning about prefix `bot` — compare leaf exactly, not endswith.
        prefix_leaf = prefix.rsplit("/", 1)[-1]
        if path.parent.name and prefix_leaf == path.parent.name:
            continue
        sample_refs = list(dict.fromkeys(samples[prefix]))[:3]
        yield Finding(
            file=str(path),
            line=0,
            severity=Severity.INFO,
            code="splitting-candidate",
            message=(
                f"{count} gotcha bullets reference paths under `{prefix}/` — "
                f"consider promoting to `{prefix}/AGENTS.md`"
            ),
            hint=f"sample refs: {', '.join(sample_refs)}",
        )
