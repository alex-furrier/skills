"""One frontmatter parser. Replaces the two hand-rolled parsers in the codebase.

We don't pull in PyYAML — the schema is tightly constrained (kebab-cased top-level
keys, optional scalar values, optional list of inline dicts). This parser handles
everything the plugin emits and nothing more.
"""

from __future__ import annotations

import re

_TOP_KEY_RE = re.compile(r"^([a-z][a-z0-9_-]*):\s*(.*)$")


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body). `None` if content has no frontmatter."""
    if not content.startswith("---"):
        return None, content

    end = content.find("\n---", 3)
    if end == -1:
        return None, content

    raw = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")

    fm: dict = {}
    current_key: str | None = None
    current_list: list | None = None

    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        top = _TOP_KEY_RE.match(line) if not line.startswith(" ") else None
        if top:
            if current_key is not None and current_list is not None:
                fm[current_key] = current_list
                current_list = None

            key, value = top.group(1), top.group(2).strip()
            if value == "":
                current_key = key
                current_list = None
            elif value == "[]":
                fm[key] = []
                current_key = key
                current_list = None
            else:
                fm[key] = value
                current_key = key
                current_list = None
            continue

        stripped = line.strip()
        if stripped.startswith("- ") and current_key is not None:
            item = stripped[2:].strip()
            if current_list is None:
                current_list = []
            if ":" in item and item.split(":", 1)[0].strip().isidentifier():
                # Inline dict entry like `- id: foo`
                k, _, v = item.partition(":")
                current_list.append({k.strip(): v.strip()})
            else:
                current_list.append(item)

    if current_key is not None and current_list is not None:
        fm[current_key] = current_list

    return fm, body
