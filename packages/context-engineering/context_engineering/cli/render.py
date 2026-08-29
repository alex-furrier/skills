"""Render LintResult / AnalysisResult as JSON or human-readable text."""

from __future__ import annotations

import json
import sys
from typing import Any

from ..domain.finding import Severity
from ..domain.result import AnalysisResult, LintResult


def emit_json(result: Any) -> None:
    json.dump(result.to_dict(), sys.stdout, indent=2, default=str, sort_keys=False)
    sys.stdout.write("\n")


def render_lint(result: LintResult) -> int:
    """Print a LintResult in human-readable form. Return suggested exit code."""
    if not result.findings:
        print(f"No findings in {result.target}")
        return 0

    by_severity = {Severity.ERROR: [], Severity.WARNING: [], Severity.INFO: []}
    for finding in result.findings:
        by_severity[finding.severity].append(finding)

    summary = (
        f"{result.error_count} error(s), "
        f"{result.warning_count} warning(s), "
        f"{result.info_count} info"
    )
    print(f"{summary} in {result.target}\n")

    for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        for f in by_severity[severity]:
            where = f"{f.file}:{f.line}" if f.line > 0 else f.file
            print(f"  [{f.severity.value}] {where} [{f.code}] {f.message}")
            if f.hint:
                print(f"    hint: {f.hint}")
        if by_severity[severity]:
            print()

    return 1 if result.has_errors else 0


def render_analysis(result: AnalysisResult) -> int:
    """Print an AnalysisResult. Key-value or tabular depending on shape."""
    data = result.data
    print(f"Target: {result.target}")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            print(f"{key}:")
            _print_nested(value, indent=2)
        else:
            print(f"{key}: {value}")

    # Surface any warnings/errors that came along with the analysis (e.g.,
    # cross-cutting's "skipping outside-repo path" warnings). Previously these
    # showed up in --json but not in the human-readable output.
    if result.findings:
        print()
        print(f"Findings ({len(result.findings)}):")
        for f in result.findings:
            where = f"{f.file}:{f.line}" if f.line > 0 else f.file
            print(f"  [{f.severity.value}] {where} [{f.code}] {f.message}")
            if f.hint:
                print(f"    hint: {f.hint}")
    return 0


def _print_nested(value, indent: int) -> None:
    pad = " " * indent
    if isinstance(value, list):
        for item in value[:20]:
            if isinstance(item, dict):
                print(pad + "- " + ", ".join(f"{k}={v}" for k, v in item.items()))
            else:
                print(f"{pad}- {item}")
        if len(value) > 20:
            print(f"{pad}... {len(value) - 20} more items; rerun with --json for all")
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                print(f"{pad}{k}:")
                _print_nested(v, indent + 2)
            else:
                print(f"{pad}{k}: {v}")
