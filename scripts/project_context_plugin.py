#!/usr/bin/env python3
"""Project canonical Context skills and CLI into the Claude plugin artifact."""
from __future__ import annotations

import argparse
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAIRS = (
    (ROOT / "skills/context-engineering", ROOT / "plugins/context-engineering/skills"),
    (ROOT / "packages/context-engineering/src", ROOT / "plugins/context-engineering/cli/src"),
)
FILES = (
    (ROOT / "packages/context-engineering/pyproject.toml", ROOT / "plugins/context-engineering/cli/pyproject.toml"),
    (ROOT / "packages/context-engineering/uv.lock", ROOT / "plugins/context-engineering/cli/uv.lock"),
)


def same_tree(source: pathlib.Path, destination: pathlib.Path) -> bool:
    comparison = filecmp.dircmp(source, destination)
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    return all(same_tree(source / name, destination / name) for name in comparison.common_dirs)


def project() -> None:
    for source, destination in PAIRS:
        shutil.rmtree(destination)
        shutil.copytree(source, destination)
    for source, destination in FILES:
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the plugin is not an exact projection")
    args = parser.parse_args()
    current = all(same_tree(source, destination) for source, destination in PAIRS) and all(
        source.read_bytes() == destination.read_bytes() for source, destination in FILES
    )
    if args.check:
        if not current:
            print("Context plugin projection is stale; run python scripts/project_context_plugin.py")
            return 1
        print("Context plugin projection is current")
        return 0
    project()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
