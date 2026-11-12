"""Subprocess helpers with explicit failure behavior."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    """Captured process result."""

    returncode: int
    stdout: str
    stderr: str


def run(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int = 180,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    """Run a non-interactive subprocess and capture separate streams."""
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=process_env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except OSError as error:
        raise RuntimeError(f"failed to execute {command[0]}: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{command[0]} exceeded {timeout_seconds} seconds") from error
    return ProcessResult(completed.returncode, completed.stdout, completed.stderr)
