#!/usr/bin/env python3
"""Run explicitly supplied Writing Check candidates in one Python process.

This caller intentionally does not discover repository files or alter the
single-candidate checker contract. It emits one unchanged schema-3 JSON record
per input candidate (JSON Lines).
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
from typing import Any, Callable, Protocol, TypeAlias, cast

CHECKER_PATH = pathlib.Path(__file__).with_name("writing_check.py")
ProbeFailure: TypeAlias = OSError | subprocess.TimeoutExpired
ProbeResult: TypeAlias = subprocess.CompletedProcess[bytes] | ProbeFailure


class _SubprocessModule(Protocol):
    run: Callable[..., subprocess.CompletedProcess[bytes]]


class _Checker(Protocol):
    subprocess: _SubprocessModule

    def main(self) -> int: ...


def _load_checker() -> _Checker:
    spec = importlib.util.spec_from_file_location("writing_check_for_sweep", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load writing_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(_Checker, module)


def _input_error(message: str) -> dict[str, Any]:
    return {
        "schema": 3,
        "status": "input_error",
        "error": {"code": "invalid_candidates", "message": message},
    }


def _candidates(path: pathlib.Path) -> list[tuple[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read candidates: {error}") from error
    if not isinstance(data, list) or not data:
        raise ValueError("candidates must be a non-empty JSON array")
    result: list[tuple[str, str]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict) or set(item) != {"source", "profile"}:
            raise ValueError(f"candidate {index} must contain exactly source and profile")
        source, profile = item["source"], item["profile"]
        if not isinstance(source, str) or not source or source == "-" or not isinstance(profile, str):
            raise ValueError(f"candidate {index} has an invalid source or profile")
        result.append((source, profile))
    return result


def run(candidates: list[tuple[str, str]]) -> tuple[list[dict[str, Any]], int]:
    """Return independent checker records while sharing only Vale version probing."""
    checker = _load_checker()
    original_run = checker.subprocess.run
    cached_versions: dict[tuple[str, ...], ProbeResult] = {}

    def cached_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        if argv[1:] != ["--version"]:
            return original_run(argv, **kwargs)
        key = tuple(argv)
        if key not in cached_versions:
            try:
                cached_versions[key] = original_run(argv, **kwargs)
            except (OSError, subprocess.TimeoutExpired) as error:  # checker serializes its own probe failure
                cached_versions[key] = error
        cached_version = cached_versions[key]
        if isinstance(cached_version, (OSError, subprocess.TimeoutExpired)):
            raise cached_version
        return cached_version

    checker.subprocess.run = cached_run
    records: list[dict[str, Any]] = []
    exit_code = 0
    old_argv = sys.argv
    try:
        for source, profile in candidates:
            output = io.StringIO()
            sys.argv = [str(CHECKER_PATH), "--profile", profile, "--json", "--", source]
            with contextlib.redirect_stdout(output):
                code = checker.main()
            records.append(json.loads(output.getvalue()))
            exit_code = max(exit_code, code)
    finally:
        sys.argv = old_argv
        checker.subprocess.run = original_run
    return records, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="bounded explicit Writing Check sweep")
    parser.add_argument("--candidates", required=True, metavar="JSON", help="JSON array of exact {source, profile} pairs")
    parser.add_argument("--jsonl", action="store_true", required=True, help="emit one schema-3 record per line")
    args = parser.parse_args()
    try:
        candidates = _candidates(pathlib.Path(args.candidates))
    except ValueError as error:
        print(json.dumps(_input_error(str(error))))
        return 2
    records, code = run(candidates)
    for record in records:
        print(json.dumps(record))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
