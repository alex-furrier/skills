"""Read an exact Git tree through a temporary, disposable filesystem view."""

from __future__ import annotations

import os
import posixpath
import stat
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory


@dataclass(frozen=True)
class _TreeEntry:
    mode: str
    object_id: str
    path: str


def _tree_entries(repo: Path, commit: str) -> tuple[list[_TreeEntry], str | None]:
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--full-tree", commit],
            cwd=repo,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"could not read Git tree: {exc}"
    if result.returncode != 0:
        message = os.fsdecode(result.stderr).strip() or "git ls-tree failed"
        return [], message
    entries: list[_TreeEntry] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            return [], "git ls-tree returned a malformed record"
        mode, object_type, object_id = (os.fsdecode(field) for field in fields)
        path = os.fsdecode(raw_path)
        pure = PurePosixPath(path)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            return [], f"git tree contains an unsafe path: {path!r}"
        if object_type == "blob":
            entries.append(_TreeEntry(mode=mode, object_id=object_id, path=path))
        elif mode == "160000":
            entries.append(_TreeEntry(mode=mode, object_id=object_id, path=path))
    return entries, None


def _read_blobs(
    repo: Path, entries: list[_TreeEntry]
) -> tuple[dict[str, bytes], str | None]:
    object_ids = list(dict.fromkeys(entry.object_id for entry in entries if entry.mode != "160000"))
    if not object_ids:
        return {}, None
    try:
        result = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=repo,
            input=("\n".join(object_ids) + "\n").encode(),
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {}, f"could not read Git blobs: {exc}"
    if result.returncode != 0:
        message = os.fsdecode(result.stderr).strip() or "git cat-file failed"
        return {}, message
    blobs: dict[str, bytes] = {}
    output = result.stdout
    offset = 0
    for expected in object_ids:
        newline = output.find(b"\n", offset)
        if newline < 0:
            return {}, "git cat-file returned a truncated header"
        fields = output[offset:newline].split()
        if len(fields) != 3 or os.fsdecode(fields[0]) != expected or fields[1] != b"blob":
            return {}, "git cat-file returned unexpected object metadata"
        try:
            size = int(fields[2])
        except ValueError:
            return {}, "git cat-file returned an invalid blob size"
        start = newline + 1
        end = start + size
        if end >= len(output) or output[end : end + 1] != b"\n":
            return {}, "git cat-file returned truncated blob content"
        blobs[expected] = output[start:end]
        offset = end + 1
    if offset != len(output):
        return {}, "git cat-file returned trailing data"
    return blobs, None


@contextmanager
def materialize_tree(repo: Path, commit: str) -> Iterator[tuple[Path | None, str | None]]:
    """Yield tracked tree bytes without checkout filters or archive attributes."""
    entries, entry_error = _tree_entries(repo, commit)
    if entry_error:
        yield None, entry_error
        return
    blobs, blob_error = _read_blobs(repo, entries)
    if blob_error:
        yield None, blob_error
        return
    with TemporaryDirectory(prefix="context-engineering-tree-") as temporary:
        root = Path(temporary)
        try:
            for entry in entries:
                target = root.joinpath(*PurePosixPath(entry.path).parts)
                if entry.mode == "160000":
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                content = blobs[entry.object_id]
                if entry.mode == "120000":
                    link_text = os.fsdecode(content)
                    link = PurePosixPath(link_text)
                    normalized = posixpath.normpath(
                        str(PurePosixPath(entry.path).parent / link)
                    )
                    if link.is_absolute() or normalized == ".." or normalized.startswith("../"):
                        raise OSError(f"tracked symlink escapes the Git tree: {entry.path!r}")
                    target.symlink_to(link_text)
                    continue
                target.write_bytes(content)
                if entry.mode == "100755":
                    target.chmod(target.stat().st_mode | stat.S_IXUSR)
        except OSError as exc:
            yield None, f"could not materialize Git tree: {exc}"
            return
        yield root, None
