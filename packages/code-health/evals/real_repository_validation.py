#!/usr/bin/env python3
"""Opt-in real-repository validation for the TypeScript and Go adapters.

This is intentionally a calibration harness, not part of the deterministic CLI
suite. It clones pinned public source into caller-selected disposable state and
requires all provisioning to be visible in its command transcript.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TYPESCRIPT_REPOSITORY = "https://github.com/safurrier/pi-sprite.git"
TYPESCRIPT_REVISION = "52aeed091ad85ec9e20bf2cf1511480570ea0263"
GO_REPOSITORY = "https://github.com/segmentio/ksuid.git"
GO_REVISION = "d33724947fcfba7949906c2b1821e96a1c8d06e7"
ESLINT_VERSION = "9.39.1"
TYPESCRIPT_PARSER_VERSION = "8.49.0"
GOLANGCI_VERSION = "2.1.0"
REVISION = re.compile(r"[0-9a-f]{40}")
GOLANGCI_VERSION_OUTPUT = re.compile(r"\bversion\s+(\d+\.\d+\.\d+)\b", re.I)
EXACT_VERSION_OUTPUT = re.compile(r"v?(\d+\.\d+\.\d+)")


@dataclass(frozen=True)
class Case:
    """One pinned source and the analyzer it must exercise."""

    name: str
    repository: str
    revision: str
    language: str
    tool: str


CASES = (
    Case("pi-sprite", TYPESCRIPT_REPOSITORY, TYPESCRIPT_REVISION, "typescript", "eslint"),
    Case("ksuid", GO_REPOSITORY, GO_REVISION, "go", "golangci-lint"),
)


def command(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run one visible command and fail before an external error can false-pass."""
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return result


def pinned_golangci_version() -> str:
    """Require the calibration binary to match its documented exact pin."""
    result = command("golangci-lint", "version")
    output = (result.stdout + result.stderr).strip()
    match = GOLANGCI_VERSION_OUTPUT.search(output)
    if match is None:
        raise RuntimeError(f"cannot parse golangci-lint version output: {output or 'empty output'}")
    version = match.group(1)
    if version != GOLANGCI_VERSION:
        raise RuntimeError(
            f"golangci-lint {GOLANGCI_VERSION} is required for calibration; found {version}"
        )
    return version


def clean_tree(repository: Path) -> None:
    """Reject any tracked or non-ignored source change in a disposable clone."""
    status = command("git", "status", "--porcelain=v1", "--untracked-files=all", cwd=repository)
    if status.stdout:
        raise RuntimeError(f"{repository} changed during validation: {status.stdout.strip()}")
    command("git", "diff", "--exit-code", cwd=repository)
    command("git", "diff", "--cached", "--exit-code", cwd=repository)


def clone(case: Case, workdir: Path) -> Path:
    if not REVISION.fullmatch(case.revision):
        raise ValueError(f"{case.name} revision must be a full 40-character SHA")
    destination = workdir / case.name
    if destination.exists():
        raise RuntimeError(f"disposable destination already exists: {destination}")
    command("git", "clone", "--no-checkout", case.repository, str(destination))
    command("git", "checkout", "--detach", case.revision, cwd=destination)
    actual = command("git", "rev-parse", "HEAD", cwd=destination).stdout.strip()
    if actual != case.revision:
        raise RuntimeError(f"{case.name} checkout is {actual}, expected pinned {case.revision}")
    clean_tree(destination)
    return destination


def exact_version(output: str, tool: str, expected: str) -> str:
    """Parse one exact tool version, allowing only ESLint's leading ``v``."""
    match = EXACT_VERSION_OUTPUT.fullmatch(output.strip())
    if match is None:
        raise RuntimeError(
            f"cannot parse {tool} version output: {output.strip() or 'empty output'}"
        )
    version = match.group(1)
    if version != expected:
        raise RuntimeError(f"{tool} {expected} is required for calibration; found {version}")
    return version


def pinned_typescript_versions(repository: Path) -> dict[str, str]:
    """Require the disposable candidate's resolved ESLint and parser pins."""
    eslint = exact_version(
        command(
            str(repository / "node_modules" / ".bin" / "eslint"), "--version", cwd=repository
        ).stdout,
        "eslint",
        ESLINT_VERSION,
    )
    parser_path = Path(
        command(
            "node",
            "-p",
            "require.resolve('@typescript-eslint/parser/package.json')",
            cwd=repository,
        ).stdout.strip()
    ).resolve()
    candidate_modules = (repository / "node_modules").resolve()
    if not parser_path.is_file() or candidate_modules not in parser_path.parents:
        raise RuntimeError(
            f"cannot resolve candidate-local @typescript-eslint/parser metadata: {parser_path}"
        )
    try:
        parser_version = json.loads(parser_path.read_text())["version"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(
            f"cannot parse @typescript-eslint/parser package metadata: {parser_path}"
        ) from error
    if not isinstance(parser_version, str) or parser_version != TYPESCRIPT_PARSER_VERSION:
        raise RuntimeError(
            "@typescript-eslint/parser "
            f"{TYPESCRIPT_PARSER_VERSION} is required for calibration; found {parser_version!r}"
        )
    return {"eslint": eslint, "@typescript-eslint/parser": parser_version}


def provision_typescript(repository: Path) -> None:
    """Install and verify only disposable ESLint dependencies without package-file changes."""
    command(
        "npm",
        "install",
        "--no-save",
        "--package-lock=false",
        "--ignore-scripts",
        f"eslint@{ESLINT_VERSION}",
        f"@typescript-eslint/parser@{TYPESCRIPT_PARSER_VERSION}",
        cwd=repository,
    )
    pinned_typescript_versions(repository)
    clean_tree(repository)


def run_report(cli: Path, mode: str, repository: Path) -> dict[str, Any]:
    result = (
        command(
            sys.executable,
            "-m",
            "code_health",
            mode,
            str(repository),
            "--base",
            "HEAD",
            "--format",
            "json",
            cwd=cli,
        )
        if mode == "diff"
        else command(
            sys.executable,
            "-m",
            "code_health",
            mode,
            str(repository),
            "--format",
            "json",
            cwd=cli,
        )
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"code-health {mode} did not produce JSON: {error}") from error


def validate_report(case: Case, mode: str, report: dict[str, Any]) -> dict[str, Any]:
    if report.get("status") != "ok":
        raise RuntimeError(f"{case.name} {mode} status is {report.get('status')!r}, expected 'ok'")
    if case.language not in report.get("languages", []):
        raise RuntimeError(f"{case.name} {mode} languages are {report.get('languages')!r}")
    tools = report.get("tools", [])
    matching = [tool for tool in tools if tool.get("tool") == case.tool]
    if len(matching) < 2 or any(tool.get("status") != "ok" for tool in matching):
        raise RuntimeError(
            f"{case.name} {mode} lacks successful {case.tool} provenance: {matching!r}"
        )
    findings = report.get("findings")
    if not isinstance(findings, list) or not findings:
        raise RuntimeError(f"{case.name} {mode} produced no analyzer findings")
    if not any(finding.get("tool") == case.tool for finding in findings):
        raise RuntimeError(f"{case.name} {mode} produced no {case.tool} findings")
    if mode == "diff":
        deltas = report.get("deltas")
        if (
            not isinstance(deltas, list)
            or not deltas
            or any(delta.get("status") != "unchanged" for delta in deltas)
        ):
            raise RuntimeError(f"{case.name} exact-HEAD diff must produce unchanged deltas")
    return {
        "mode": mode,
        "findings": len(findings),
        "deltas": len(report.get("deltas", [])),
        "tool": matching[-1],
    }


def validate_case(case: Case, workdir: Path, cli: Path) -> dict[str, Any]:
    repository = clone(case, workdir)
    if case.language == "typescript":
        provision_typescript(repository)
    reports = {
        mode: validate_report(case, mode, run_report(cli, mode, repository))
        for mode in ("scan", "diff")
    }
    clean_tree(repository)
    return {"repository": case.repository, "revision": case.revision, "reports": reports}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run opt-in pinned real-repository calibration.")
    parser.add_argument("--workdir", type=Path, required=True, help="Empty disposable directory.")
    parser.add_argument(
        "--cli", type=Path, default=Path(__file__).parents[1], help="CLI project directory."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workdir = args.workdir.resolve()
    if workdir.exists() and any(workdir.iterdir()):
        print(f"error: --workdir must be empty: {workdir}", file=sys.stderr)
        return 2
    workdir.mkdir(parents=True, exist_ok=True)
    if not (args.cli / "pyproject.toml").is_file():
        print(f"error: --cli is not the code-health CLI project: {args.cli}", file=sys.stderr)
        return 2
    try:
        pinned_golangci_version()
        result = {case.name: validate_case(case, workdir, args.cli.resolve()) for case in CASES}
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "pins": {
                    "eslint": ESLINT_VERSION,
                    "@typescript-eslint/parser": TYPESCRIPT_PARSER_VERSION,
                    "golangci-lint": GOLANGCI_VERSION,
                },
                "cases": result,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
