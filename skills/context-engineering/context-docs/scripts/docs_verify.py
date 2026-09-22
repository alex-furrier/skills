#!/usr/bin/env python3
"""Run installed Context CLI documentation checks and emit one JSON record."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKS = ("frontmatter", "references")


def emit(record: dict[str, object], status: int) -> int:
    print(json.dumps(record, sort_keys=True))
    return status


def main() -> int:
    root = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()).resolve()
    results: dict[str, dict[str, object]] = {}
    for check in CHECKS:
        try:
            result = subprocess.run(
                ["context-engineering", check, str(root), "--json"],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return emit(
                {
                    "schema": 1,
                    "target": str(root),
                    "context_cli": "unavailable",
                    "reason": "Install the independently distributed Context CLI, then rerun this verifier.",
                    "findings": [],
                },
                3,
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return emit(
                {
                    "schema": 1,
                    "target": str(root),
                    "context_cli": "execution_error",
                    "reason": f"context-engineering {check} did not return JSON",
                    "findings": [],
                },
                4,
            )
        results[check] = payload

    findings = [
        finding
        for payload in results.values()
        for finding in payload.get("findings", [])
    ]
    return emit(
        {
            "schema": 1,
            "target": str(root),
            "context_cli": "available",
            "checks": results,
            "findings": findings,
        },
        1 if any(payload.get("summary", {}).get("error", 0) for payload in results.values()) else 0,
    )


if __name__ == "__main__":
    raise SystemExit(main())
