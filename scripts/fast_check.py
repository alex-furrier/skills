#!/usr/bin/env python3
"""Run complete local validation for the portable catalog."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str, allowed_returncodes: tuple[int, ...] = (0,)) -> None:
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode not in allowed_returncodes:
        raise SystemExit(f"{' '.join(command)} exited {result.returncode}")


def main() -> None:
    run("python", "scripts/project_context_plugin.py", "--check")
    run("python", "scripts/project_thinking_plugin.py", "--check")
    run("uv", "lock", "--no-config", "--project", "packages/context-engineering", "--check", "--offline")
    run("uv", "lock", "--no-config", "--project", "packages/writing-check", "--check", "--offline")
    run("uv", "run", "--python", "3.11", "--with", "pytest", "--with", "mkdocs", "pytest", "-q")
    run("uv", "run", "--python", "3.11", "--with", "mkdocs", "mkdocs", "build", "--strict")
    run(
        "uv",
        "run",
        "--project",
        "packages/writing-check",
        "writing-check",
        "--profile",
        "readme",
        "--json",
        "README.md",
        allowed_returncodes=(0, 1),
    )
    run("python", "scripts/validate.py")
    run("python", "scripts/validate_evals.py")
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
