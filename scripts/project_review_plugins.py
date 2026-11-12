#!/usr/bin/env python3
"""Generate Code Quality and Writing plugins from canonical suite sources."""
from __future__ import annotations

import argparse
from pathlib import Path

from project_thinking_plugin import check, encoded

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    "code-quality": "Proportional code review, architecture, code health and test audits",
    "writing": "Destination-aware writing, editing and advisory style checks",
}
VERSION = "0.1.0"
LOCAL_ARTIFACT_NAMES = frozenset({
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", ".DS_Store", ".cache", ".tox", ".nox",
    ".hypothesis", ".git", ".coverage", "htmlcov",
})


def excluded(path: Path) -> bool:
    """Identify local environments and generated caches in a suite-relative path."""
    return any(part in LOCAL_ARTIFACT_NAMES for part in path.parts) or path.suffix in {".pyc", ".pyo"}


def build(root: Path, suite: str) -> dict[str, bytes]:
    source = root / "skills" / suite
    if source.is_symlink():
        raise ValueError(f"Symlinked canonical suite: {source}")
    names = sorted(
        path.name for path in source.iterdir()
        if not excluded(path.relative_to(source)) and path.is_dir()
    )
    files = {
        ".claude-plugin/plugin.json": encoded({
            "name": suite, "version": VERSION, "description": SUITES[suite],
            "skills": [f"./skills/{name}" for name in names],
        }),
        "LICENSE": (root / "LICENSE").read_bytes(),
        "provenance.json": encoded({
            "schema": 1,
            "decision": f"Generated exact projection of skills/{suite} in alex-furrier/skills. Per-skill licenses and provenance travel with the bundle. Companion CLIs are not bundled.",
            "entries": [
                {"path_prefix": "skills/", "origin": f"canonical skills/{suite}, including source provenance", "license": "MIT"},
                {"path_prefix": ".claude-plugin/", "origin": "generated plugin metadata", "license": "MIT"},
                {"path": "LICENSE", "origin": "catalog MIT license", "license": "MIT"},
                {"path": "provenance.json", "origin": "generated plugin inventory", "license": "MIT"},
            ],
        }),
    }
    for path in sorted(source.rglob("*")):
        if excluded(path.relative_to(source)):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink in canonical suite: {path}")
        if path.is_file():
            files[f"skills/{path.relative_to(source).as_posix()}"] = path.read_bytes()
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for suite in SUITES:
        files = build(ROOT, suite)
        destination = ROOT / "plugins" / suite
        if args.check:
            if not check(files, destination):
                print(f"{suite} projection is stale; run python scripts/project_review_plugins.py")
                return 1
            print(f"{suite} plugin projection is current")
            continue
        if destination.is_symlink():
            raise ValueError(f"Symlinked destination: {destination}")
        for path in destination.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink in destination: {path}")
            if path.is_file() and path.relative_to(destination).as_posix() not in files:
                path.unlink()
        for relative, data in files.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
