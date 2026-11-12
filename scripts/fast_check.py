#!/usr/bin/env python3
"""Run complete local validation for the portable catalog."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"{' '.join(command)} exited {result.returncode}")


def run_readme_check() -> None:
    """Require usable exact-source evidence, accepting advisory findings."""
    result = subprocess.run(
        ["uv", "run", "--python", "3.11", "--project", "packages/writing-check", "writing-check",
         "--profile", "readme", "--json", "README.md"],
        cwd=ROOT, capture_output=True, text=True,
    )
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    try:
        record = json.loads(result.stdout)
        data = (ROOT / "README.md").read_bytes()
        expected_status = {0: "no_findings", 1: "findings"}.get(result.returncode)
        if not isinstance(record, dict) or expected_status is None:
            raise ValueError("invalid record or process exit")
        source, vale, alerts = record.get("source"), record.get("vale"), record.get("alerts")
        if not (
            record.get("schema") == 3 and record.get("profile") == "readme"
            and record.get("advisory") is True and record.get("status") == expected_status
            and isinstance(alerts, list) and bool(alerts) == (expected_status == "findings")
            and isinstance(vale, dict) and vale.get("status") == "ran"
            and isinstance(source, dict) and source.get("kind") == "file"
            and source.get("identifier") == str((ROOT / "README.md").resolve())
            and source.get("text") == data.decode("utf-8") and source.get("bytes") == len(data)
            and source.get("sha256") == hashlib.sha256(data).hexdigest()
        ):
            raise ValueError("unusable or mismatched source-bound record")
    except (OSError, UnicodeError, ValueError) as error:
        raise SystemExit(f"README Writing Check evidence failed validation: {error}") from error


def check_code_quality_portability() -> None:
    """Reject private execution plumbing, not provenance or legal attribution."""
    forbidden = re.compile(
        r"\bDots\b|\bPi\s+(?:subagent\w*|tools?)\b|native-pi|codemode|"
        r"ai[-_]runtime|Groundskeeper|Harness Kit|~[/]\.agent|"
        r"alex-ai(?:-experimental)?|[/]Users[/]|[/]home[/][^/]+[/]",
        re.IGNORECASE,
    )
    for directory in ("skills/code-quality", "packages/code-health"):
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file() or any(part in {".venv", "__pycache__", ".pytest_cache", "dist"} for part in path.parts):
                continue
            if path.name in {"provenance.json", "LICENSE", "THIRD_PARTY_NOTICES.md", "uv.lock"}:
                continue
            if path.suffix in {".md", ".py", ".toml"} and forbidden.search(path.read_text()):
                raise SystemExit(f"removed execution plumbing in {path.relative_to(ROOT)}")


def main() -> None:
    check_code_quality_portability()
    run("uv", "lock", "--no-config", "--project", "packages/code-health", "--check", "--offline")
    run("uv", "run", "--frozen", "--python", "3.11", "--project", "packages/code-health", "pytest", "-q", "packages/code-health/tests")
    run("python", "scripts/project_context_plugin.py", "--check")
    run("python", "scripts/project_thinking_plugin.py", "--check")
    run("uv", "lock", "--no-config", "--project", "packages/context-engineering", "--check", "--offline")
    run("uv", "lock", "--no-config", "--project", "packages/writing-check", "--check", "--offline")
    run("uv", "run", "--python", "3.11", "--with", "pytest", "--with", "mkdocs", "pytest", "-q", "tests")
    run("uv", "run", "--python", "3.11", "--with", "mkdocs", "mkdocs", "build", "--strict")
    run_readme_check()
    run("python", "scripts/validate.py")
    run("python", "scripts/validate_evals.py")
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
