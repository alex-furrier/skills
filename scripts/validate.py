#!/usr/bin/env python3
"""Validate portable catalog metadata, links, packages, and projections."""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT = {".md", ".py", ".json", ".yml", ".yaml", ".toml", ".ini"}
IGNORED = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "site", "dist"}
PRIVATE = (r"/Users/", r"/home/[^/]+/", r"\.pi-personal", r"AI_RUNTIME_PROFILE", r"DISCORD", r"HPPM", r"obsidian")


def covered(path: str, entries: list[dict[str, str]]) -> bool:
    return any(path == item.get("path") or path.startswith(item.get("path_prefix", "\0")) for item in entries)


def main() -> int:
    errors: list[str] = []
    try:
        inventory = json.loads((ROOT / "provenance.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid provenance: {error}")
        return 1
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        errors.append("provenance has no entries")
    else:
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if any(part in IGNORED for part in relative.parts) or not path.is_file():
                continue
            name = relative.as_posix()
            if not covered(name, entries):
                errors.append(f"provenance missing shipped path: {name}")
            if path.suffix in TEXT and name not in {"provenance.json", "scripts/validate.py"} and not name.startswith("tests/"):
                text = path.read_text(encoding="utf-8")
                if any(re.search(token, text, re.I) for token in PRIVATE):
                    errors.append(f"private token in {name}")
    skills = list((ROOT / "skills").glob("*/*/SKILL.md"))
    for skill in skills:
        match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: .+\n---", skill.read_text(), re.S)
        if not match or match.group(1) != skill.parent.name:
            errors.append(f"invalid skill metadata: {skill.relative_to(ROOT)}")
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORED for part in path.relative_to(ROOT).parts):
            continue
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text(encoding="utf-8")):
            if "://" not in target and not (path.parent / target).exists():
                errors.append(f"missing link: {path.relative_to(ROOT)} -> {target}")
    result = subprocess.run([sys.executable, "scripts/project_context_plugin.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        errors.append(result.stdout.strip())
    print("\n".join(errors) if errors else "validation passed")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
