#!/usr/bin/env python3
"""Run plugin deterministic documentation checks; fail when the plugin is incomplete."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def emit(record: dict[str, object], status: int) -> int:
    print(json.dumps(record, sort_keys=True))
    return status


def main() -> int:
    root = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()).resolve()
    plugin_root = Path(__file__).resolve().parents[3]
    package_root = plugin_root / "cli" / "src"
    if not (package_root / "context_engineering").is_dir():
        return emit(
            {
                "schema": 1,
                "target": str(root),
                "context_cli": "unavailable",
                "reason": "Install the complete Context plugin with cli/; a copied Context skill cannot provide deterministic verification.",
                "findings": [],
            },
            3,
        )

    sys.path.insert(0, str(package_root))
    from context_engineering.analysis.context_layout import discover
    from context_engineering.checks.frontmatter import lint as lint_frontmatter
    from context_engineering.checks.references import lint as lint_references

    findings = [*lint_frontmatter(root).findings, *lint_references(root).findings]
    return emit(
        {
            "schema": 1,
            "target": str(root),
            "context_cli": "available",
            "docs_trees": len(discover(root).docs_trees),
            "findings": [
                {"code": item.code, "file": item.file, "message": item.message}
                for item in sorted(findings, key=lambda finding: (finding.file, finding.code))
            ],
        },
        1 if findings else 0,
    )


if __name__ == "__main__":
    raise SystemExit(main())
