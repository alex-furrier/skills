"""Shared Markdown visibility helpers for deterministic context checks."""

from __future__ import annotations

import re

_HTML_COMMENT_RE = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)


def _masked_line(line: str) -> str:
    return "".join(
        "\n" if character == "\n" else "\r" if character == "\r" else " " for character in line
    )


def _fence_marker(line: str) -> tuple[str, int] | None:
    text = line.rstrip("\r\n")
    indentation = len(text) - len(text.lstrip(" "))
    if indentation > 3:
        return None
    body = text[indentation:]
    if not body or body[0] not in {"`", "~"}:
        return None
    marker = body[0]
    length = len(body) - len(body.lstrip(marker))
    return (marker, length) if length >= 3 else None


def _closes_fence(line: str, marker: str, minimum_length: int) -> bool:
    text = line.rstrip("\r\n")
    indentation = len(text) - len(text.lstrip(" "))
    if indentation > 3:
        return False
    body = text[indentation:]
    length = len(body) - len(body.lstrip(marker))
    return length >= minimum_length and not body[length:].strip()


def mask_invisible_markdown(content: str) -> str:
    """Replace fenced blocks and HTML comments while preserving line positions."""
    visible: list[str] = []
    marker: str | None = None
    minimum_length = 0
    for line in content.splitlines(keepends=True):
        if marker is not None:
            visible.append(_masked_line(line))
            if _closes_fence(line, marker, minimum_length):
                marker = None
                minimum_length = 0
            continue
        opening = _fence_marker(line)
        if opening is None:
            visible.append(line)
            continue
        marker, minimum_length = opening
        visible.append(_masked_line(line))
    without_fences = "".join(visible)
    return _HTML_COMMENT_RE.sub(lambda match: _masked_line(match.group(0)), without_fences)
