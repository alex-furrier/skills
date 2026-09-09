#!/usr/bin/env python3
"""Run the complete local release validation from the catalog root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str, allowed_returncodes: tuple[int, ...] = (0,)) -> None:
    """Run a required check and stop unless it produces an allowed result."""
    try:
        result = subprocess.run(command, cwd=ROOT)
    except OSError as error:
        raise SystemExit(f"{command[0]} could not run: {error}") from None
    if result.returncode not in allowed_returncodes:
        joined = " ".join(command)
        raise SystemExit(f"{joined} exited {result.returncode}")


def main() -> None:
    # This is the full local release check, not a smoke test. It intentionally
    # builds docs strictly and ignores machine-level uv resolver policy.
    run(
        "uv",
        "lock",
        "--no-config",
        "--project",
        "packages/context-engineering",
        "--check",
        "--offline",
    )
    run(
        "uv",
        "run",
        "--no-config",
        "--locked",
        "--project",
        "packages/context-engineering",
        "mypy",
        "--config-file",
        "mypy.ini",
        "packages/context-engineering/context_engineering",
        "packages/writing-check/scripts",
        "scripts",
        "skills/context/context-docs/scripts",
        "skills/writing/pr-description/scripts",
        "tests",
    )
    # The shipped Writing Check copy has the same basename as its catalog
    # implementation, so Mypy must analyze it in a separate invocation.
    run(
        "uv",
        "run",
        "--no-config",
        "--locked",
        "--project",
        "packages/context-engineering",
        "mypy",
        "--config-file",
        "mypy.ini",
        "skills/writing/writing-check/scripts/writing_check.py",
    )
    run("uv", "run", "--python", "3.11", "--with", "pytest", "--with", "mkdocs", "pytest", "-q")
    run("uv", "run", "--python", "3.11", "--with", "mkdocs", "mkdocs", "build", "--strict")
    run("uv", "run", "--python", "3.11", "python", "scripts/validate.py")
    run(
        "uv",
        "run",
        "--no-config",
        "--locked",
        "--project",
        "packages/context-engineering",
        "context-engineering",
        "references",
        ".",
        "--json",
    )
    # Writing Check findings are advisory, so a findings exit is valid release evidence.
    run(
        "uv",
        "run",
        "--python",
        "3.11",
        "python",
        "packages/writing-check/scripts/writing_check.py",
        "--profile",
        "technical-doc",
        "--json",
        "README.md",
        allowed_returncodes=(0, 1),
    )
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
