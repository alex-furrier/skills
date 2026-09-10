#!/usr/bin/env python3
"""Run complete local release validation from the catalog root."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = "plugins/context-engineering/cli"


def run(*command: str, allowed_returncodes: tuple[int, ...] = (0,)) -> None:
    try:
        result = subprocess.run(command, cwd=ROOT)
    except OSError as error:
        raise SystemExit(f"{command[0]} could not run: {error}") from None
    if result.returncode not in allowed_returncodes:
        raise SystemExit(f"{' '.join(command)} exited {result.returncode}")


def main() -> None:
    run("uv", "lock", "--no-config", "--project", CLI, "--check", "--offline")
    run(
        "uv", "run", "--no-config", "--locked", "--project", CLI, "mypy",
        "--config-file", "mypy.ini", "plugins/context-engineering/cli/src/context_engineering",
        "scripts", "plugins/context-engineering/skills/context-docs/scripts",
        "skills/writing/writing-check/scripts", "skills/writing/pr-description/scripts", "tests",
    )
    run("uv", "run", "--python", "3.11", "--with", "pytest", "--with", "mkdocs", "pytest", "-q")
    run("uv", "run", "--python", "3.11", "--with", "mkdocs", "mkdocs", "build", "--strict")
    run("uv", "run", "--python", "3.11", "python", "scripts/validate.py")
    run("uv", "run", "--no-config", "--locked", "--no-dev", "--project", CLI,
        "context-engineering", "references", ".", "--json")
    run("uv", "run", "--python", "3.11", "python",
        "skills/writing/writing-check/scripts/writing_check.py", "--profile", "technical-doc",
        "--json", "README.md", allowed_returncodes=(0, 1))
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
