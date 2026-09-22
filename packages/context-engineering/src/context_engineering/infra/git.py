"""One git wrapper. Replaces three separate git-log parsers across modules."""

from __future__ import annotations

import datetime
import subprocess
from collections.abc import Iterator
from pathlib import Path

from ..domain.commit import Commit

_COMMIT_SENTINEL = "\x1fCOMMIT\x1f"
_FIELD_SEP = "\x1f"


def resolve_commit(repo: Path, ref: str) -> tuple[str | None, str | None]:
    """Resolve ``ref`` to a full commit SHA without allowing Git options."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
            capture_output=True,
            text=True,
            cwd=repo,
        )
    except FileNotFoundError:
        return None, "Git is not installed or is not on PATH"
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or f"git rev-parse exited {result.returncode}"
        return None, diagnostic
    return result.stdout.strip(), None


def resolve_merge_base(repo: Path, base: str, head: str) -> tuple[str | None, str | None]:
    """Resolve the unique merge base used by a three-dot diff."""
    try:
        result = subprocess.run(
            ["git", "merge-base", "--", base, head],
            capture_output=True,
            text=True,
            cwd=repo,
        )
    except FileNotFoundError:
        return None, "Git is not installed or is not on PATH"
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or f"git merge-base exited {result.returncode}"
        return None, diagnostic
    candidates = result.stdout.splitlines()
    if len(candidates) != 1:
        return None, "Git did not return one merge base"
    return candidates[0], None


def git_root(path: Path) -> Path | None:
    """Return repo root for `path`, or None if not inside a git repo."""
    search = path if path.is_dir() else path.parent
    while not search.exists() and search != search.parent:
        search = search.parent
    if not search.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=search,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    reported = Path(result.stdout.strip())
    candidate = search
    while True:
        try:
            if candidate.samefile(reported):
                return candidate
        except OSError:
            pass
        if candidate == candidate.parent:
            break
        candidate = candidate.parent
    return reported


def git_log(
    repo: Path,
    *,
    since_days: int | None = None,
    since_ref: str | None = None,
    paths: list[str] | None = None,
    max_count: int | None = None,
) -> Iterator[Commit]:
    """Stream commits from `repo`, newest first.

    - `since_days`: restrict to commits within the last N days.
    - `since_ref`: restrict to `<ref>..HEAD` (commits since a specific SHA/ref).
    - `paths`: restrict to commits touching any of these paths.
    - `max_count`: cap the number of commits (for lookups like "most recent one").
    """
    root = git_root(repo)
    if root is None:
        return

    pretty = f"--pretty=format:{_COMMIT_SENTINEL}%H{_FIELD_SEP}%an{_FIELD_SEP}%aI"
    cmd = ["git", "log", "--name-only", pretty]
    if max_count is not None:
        cmd.append(f"-{max_count}")
    if since_days is not None:
        cmd.append(f"--since={since_days}.days.ago")
    if since_ref:
        cmd.append(f"{since_ref}..HEAD")
    if paths:
        cmd.append("--")
        cmd.extend(paths)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    except FileNotFoundError:
        return
    if result.returncode != 0:
        return

    yield from _parse(result.stdout)


def _parse(stdout: str) -> Iterator[Commit]:
    sha = ""
    author = ""
    date = datetime.datetime.min.replace(tzinfo=datetime.UTC)
    files: list[str] = []
    have_header = False

    for raw in stdout.splitlines():
        if raw.startswith(_COMMIT_SENTINEL):
            if have_header:
                yield Commit(sha=sha, author=author, date=date, files=tuple(files))
            header = raw[len(_COMMIT_SENTINEL) :]
            parts = header.split(_FIELD_SEP)
            if len(parts) < 3:
                have_header = False
                continue
            sha, author, date_str = parts[0], parts[1], parts[2]
            try:
                date = datetime.datetime.fromisoformat(date_str)
            except ValueError:
                date = datetime.datetime.min.replace(tzinfo=datetime.UTC)
            files = []
            have_header = True
        elif raw.strip() and have_header:
            files.append(raw.strip())

    if have_header:
        yield Commit(sha=sha, author=author, date=date, files=tuple(files))
