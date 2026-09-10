"""Byte-safe Git history and diff evidence parsing."""

from __future__ import annotations

import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict

_RECORD = b"\x1e"
_FIELD = "\x1f"
_DEFAULT_MAX_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class EvidenceBudget:
    max_records: int = 100_000
    max_paths: int = 1_000_000
    max_bytes: int = _DEFAULT_MAX_BYTES
    max_subprocesses: int = 10_000


@dataclass(frozen=True)
class EvidenceCounts:
    records: int
    paths: int
    bytes: int
    subprocesses: int = 1

    def to_dict(self) -> dict[str, int]:
        return {
            "records": self.records,
            "paths": self.paths,
            "bytes": self.bytes,
            "subprocesses": self.subprocesses,
        }


class CompletePathChange(TypedDict):
    status: str
    path: str
    old_path: NotRequired[str]


class CompleteHistoryRecord(TypedDict):
    commit: str
    date: str
    subject: str
    parents: list[str]
    changes: list[CompletePathChange]


@dataclass(frozen=True)
class HistoryRecord:
    commit: str
    date: str
    subject: str
    paths: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "commit": self.commit,
            "date": self.date,
            "subject": self.subject,
            "paths": list(self.paths),
        }


@dataclass(frozen=True)
class PathChange:
    status: str
    path: str
    old_path: str | None = None


def communicate_bounded(
    process: subprocess.Popen[bytes],
    *,
    max_bytes: int,
    timeout: float = 120,
) -> tuple[bytes, bytes, str | None]:
    """Drain stdout and stderr concurrently under one combined byte ceiling."""
    assert process.stdout is not None and process.stderr is not None
    stdout = bytearray()
    stderr = bytearray()
    lock = threading.Lock()
    exceeded = threading.Event()
    observed = 0

    def drain(stream, sink: bytearray) -> None:
        nonlocal observed
        while chunk := stream.read(64 * 1024):
            with lock:
                observed += len(chunk)
                if len(stdout) + len(stderr) <= max_bytes:
                    remaining = max_bytes + 1 - len(stdout) - len(stderr)
                    sink.extend(chunk[:remaining])
                if observed > max_bytes and not exceeded.is_set():
                    exceeded.set()
                    process.kill()

    threads = [
        threading.Thread(target=drain, args=(process.stdout, stdout), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, stderr), daemon=True),
    ]
    for thread in threads:
        thread.start()
    error: str | None = None
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        error = "Git subprocess timed out"
    for thread in threads:
        thread.join(timeout=5)
    if any(thread.is_alive() for thread in threads):
        process.kill()
        error = error or "Git subprocess streams did not close"
    if exceeded.is_set():
        error = "Git subprocess output exceeds the configured byte ceiling"
    return bytes(stdout), bytes(stderr), error


def parse_history_output(stdout: bytes) -> tuple[list[HistoryRecord], str | None]:
    """Parse NUL-delimited history without decoding repository paths as UTF-8."""
    records: list[HistoryRecord] = []
    header: tuple[str, str, str] | None = None
    paths: list[str] = []
    first_path = False
    for raw_token in stdout.split(b"\0"):
        token = raw_token
        structural = token[1:] if token.startswith(b"\n" + _RECORD) else token
        if structural.startswith(_RECORD):
            if header is not None and paths:
                records.append(HistoryRecord(*header, tuple(sorted(paths))))
            fields = os.fsdecode(structural[len(_RECORD) :]).split(_FIELD, 2)
            if len(fields) != 3:
                return [], "git log returned malformed commit metadata"
            header = (fields[0], fields[1][:10], fields[2])
            paths = []
            first_path = True
            continue
        if not token:
            continue
        if header is None:
            return [], "git log returned a path before commit metadata"
        if first_path and token.startswith(b"\n"):
            token = token[1:]
        first_path = False
        if token:
            paths.append(os.fsdecode(token))
    if header is not None and paths:
        records.append(HistoryRecord(*header, tuple(sorted(paths))))
    return records, None


def read_history(
    repo: Path,
    *,
    cutoff: str,
    relative_path: str,
    max_count: int,
) -> tuple[list[HistoryRecord], str | None]:
    command = [
        "git",
        "log",
        f"--max-count={max_count}",
        "--format=%x1e%H%x1f%aI%x1f%s",
        "--name-only",
        "-z",
        "--end-of-options",
        cutoff,
        "--",
    ]
    if relative_path != ".":
        command.append(relative_path)
    try:
        result = subprocess.run(command, cwd=repo, capture_output=True)
    except FileNotFoundError:
        return [], "Git is not installed or is not on PATH"
    if result.returncode != 0:
        diagnostic = os.fsdecode(result.stderr).strip()
        return [], diagnostic or f"git log exited {result.returncode}"
    return parse_history_output(result.stdout)


def parse_diff_output(stdout: bytes) -> tuple[list[PathChange], str | None]:
    """Parse `git diff --name-status -z` output into exact path changes."""
    tokens = stdout.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    changes: list[PathChange] = []
    index = 0
    while index < len(tokens):
        raw_status = os.fsdecode(tokens[index])
        index += 1
        if not raw_status:
            return [], "git diff returned an empty status field"
        code = raw_status[:1]
        path_count = 2 if code in {"R", "C"} else 1
        if index + path_count > len(tokens):
            return [], "git diff returned an incomplete NUL-delimited path record"
        paths = [os.fsdecode(tokens[index + offset]) for offset in range(path_count)]
        index += path_count
        changes.append(
            PathChange(
                status=raw_status,
                path=paths[-1],
                old_path=paths[0] if path_count == 2 else None,
            )
        )
    return changes, None


def read_diff(
    repo: Path,
    *,
    base: str,
    head: str,
) -> tuple[list[PathChange], str | None]:
    command = ["git", "diff", "--name-status", "-z", "--find-renames", f"{base}...{head}", "--"]
    try:
        result = subprocess.run(command, cwd=repo, capture_output=True)
    except FileNotFoundError:
        return [], "Git is not installed or is not on PATH"
    if result.returncode != 0:
        diagnostic = os.fsdecode(result.stderr).strip()
        return [], diagnostic or f"git diff exited {result.returncode}"
    return parse_diff_output(result.stdout)


def parse_complete_history_output(
    stdout: bytes,
    *,
    budget: EvidenceBudget,
) -> tuple[list[CompleteHistoryRecord], EvidenceCounts, str | None]:
    """Parse complete name-status history with explicit resource accounting."""
    records: list[CompleteHistoryRecord] = []
    current: CompleteHistoryRecord | None = None
    path_count = 0
    tokens = stdout.split(b"\0")
    index = 0
    while index < len(tokens):
        token = os.fsdecode(tokens[index])
        structural = token.lstrip("\r\n")
        if structural.startswith("\x1e"):
            if current is not None:
                records.append(current)
                if len(records) > budget.max_records:
                    counts = EvidenceCounts(len(records), path_count, len(stdout))
                    return [], counts, "history exceeds the configured record ceiling"
            fields = structural[1:].split(_FIELD, 3)
            current = None
            if len(fields) != 4:
                return (
                    [],
                    EvidenceCounts(len(records), path_count, len(stdout)),
                    ("git log returned malformed commit metadata"),
                )
            current = {
                "commit": fields[0],
                "date": fields[1][:10],
                "subject": fields[2],
                "parents": fields[3].split() if fields[3] else [],
                "changes": [],
            }
            index += 1
            continue
        status = structural
        rename_or_copy = re.fullmatch(r"[RC][0-9]+", status)
        tuple_paths = 2 if rename_or_copy else 1
        if current is None or not re.fullmatch(r"(?:[RC][0-9]+|[ACDMRTUXB]+)", status):
            index += 1
            continue
        if index + tuple_paths >= len(tokens):
            return (
                [],
                EvidenceCounts(len(records), path_count, len(stdout)),
                ("git log returned an incomplete NUL-delimited path record"),
            )
        paths = [os.fsdecode(tokens[index + offset]) for offset in range(1, tuple_paths + 1)]
        path_count += tuple_paths
        if path_count > budget.max_paths:
            counts = EvidenceCounts(len(records), path_count, len(stdout))
            return [], counts, "history exceeds the configured path ceiling"
        current["changes"].append(
            {"status": status, "path": paths[0]}
            if tuple_paths == 1
            else {"status": status, "old_path": paths[0], "path": paths[1]}
        )
        index += tuple_paths + 1
    if current is not None:
        records.append(current)
    counts = EvidenceCounts(len(records), path_count, len(stdout))
    if counts.records > budget.max_records:
        return [], counts, "history exceeds the configured record ceiling"
    return records, counts, None


def read_complete_history(
    repo: Path,
    *,
    cutoff: str,
    budget: EvidenceBudget | None = None,
) -> tuple[list[CompleteHistoryRecord], EvidenceCounts, str | None]:
    """Read complete history while stopping before unbounded stdout allocation."""
    active_budget = budget or EvidenceBudget()
    command = [
        "git",
        "log",
        "--reverse",
        "--topo-order",
        "--full-history",
        "--diff-merges=combined",
        "--find-renames=50%",
        f"--format=\x1e%H{_FIELD}%aI{_FIELD}%s{_FIELD}%P",
        "--name-status",
        "-z",
        "--end-of-options",
        cutoff,
    ]
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return [], EvidenceCounts(0, 0, 0), f"could not run Git: {exc}"
    stdout, stderr, transport_error = communicate_bounded(
        process,
        max_bytes=active_budget.max_bytes,
    )
    total_bytes = len(stdout) + len(stderr)
    if transport_error is not None:
        return (
            [],
            EvidenceCounts(0, 0, total_bytes),
            (
                "history exceeds the configured byte ceiling"
                if "ceiling" in transport_error
                else transport_error
            ),
        )
    if process.returncode != 0:
        diagnostic = os.fsdecode(stderr).strip()
        return (
            [],
            EvidenceCounts(0, 0, total_bytes),
            (diagnostic or f"git log exited {process.returncode}"),
        )
    records, counts, error = parse_complete_history_output(stdout, budget=active_budget)
    return records, EvidenceCounts(counts.records, counts.paths, total_bytes), error
