#!/usr/bin/env python3
"""Validate release metadata, portable skill metadata, links, and policy digests."""
from __future__ import annotations
import hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = (r"/Users/", r"/home/[^/]+/", r"\.pi-personal", r"AI_RUNTIME_PROFILE", r"DISCORD", r"HPPM", r"obsidian", r"\bvault\b", r"\balex\b", r"alex-", r"github-open-pr", r"writing-voice-check", r"commit-message", r"writing-editor")
TEXT = {".md", ".py", ".json", ".yml", ".yaml", ".toml", ".ini", ".sh"}
IGNORED = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "site"}


def shipped():
    for path in ROOT.rglob("*"):
        if not any(part in IGNORED for part in path.parts) and (path.is_file() or path.is_symlink()):
            yield path


def covered(rel: str, entries: list[dict[str, str]]) -> bool:
    return any(rel == entry.get("path") or rel.startswith(entry.get("path_prefix", "\0")) for entry in entries)


def validate_plugin(plugin: pathlib.Path, errors: list[str]) -> None:
    """Validate a plugin copy without relying on the catalog around it."""
    inventory_path = plugin / "provenance.json"
    try:
        inventory = json.loads(inventory_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid Context plugin provenance: {error}")
        return
    for key in ("schema", "source_revision", "decision", "entries", "excluded"):
        if not inventory.get(key): errors.append(f"Context plugin provenance missing {key}")
    entries = inventory.get("entries", [])
    for entry in entries:
        if not entry.get("origin") or not entry.get("license"):
            errors.append(f"Context plugin provenance entry lacks origin/license: {entry}")
    for required in (".claude-plugin/plugin.json", "cli/pyproject.toml", "cli/uv.lock", "skills", "LICENSE"):
        if not (plugin / required).exists(): errors.append(f"Context plugin missing required path: {required}")
    license_path = plugin / "LICENSE"
    if license_path.is_file() and "MIT License" not in license_path.read_text(encoding="utf-8"):
        errors.append("Context plugin LICENSE is not MIT license material")
    ignored = {".venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
    for path in plugin.rglob("*"):
        if any(part in ignored for part in path.parts) or not path.is_file(): continue
        rel = path.relative_to(plugin).as_posix()
        if not covered(rel, entries): errors.append(f"Context plugin provenance missing shipped path: {rel}")
        if path.suffix in TEXT and rel not in {"provenance.json"}:
            for token in PRIVATE:
                if re.search(token, path.read_text(encoding="utf-8"), re.I):
                    errors.append(f"Context plugin {rel}: private token {token}")


def validate_writing_policy(errors: list[str]) -> None:
    root = ROOT / "skills/writing/writing-check/vale"
    try:
        lock = json.loads((root / "upstream-lock.json").read_text())
        manifest = json.loads((root / "profiles.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"invalid Writing Check policy metadata: {error}")
        return
    upstream = lock.get("upstream")
    if not isinstance(upstream, dict) or not isinstance(upstream.get("license_file"), str) or not isinstance(upstream.get("license_sha256"), str):
        errors.append("invalid Writing Check license metadata")
        return
    license_path = root / upstream["license_file"]
    if not license_path.is_file():
        errors.append(f"missing Writing Check license: {license_path.relative_to(ROOT)}")
    elif hashlib.sha256(license_path.read_bytes()).hexdigest() != upstream["license_sha256"]:
        errors.append(f"Writing Check license digest mismatch: {license_path.relative_to(ROOT)}")
    rules = manifest.get("rules")
    if not isinstance(rules, dict) or not rules:
        errors.append("Writing Check manifest has no rule digests")
        return
    declared = set()
    for name, metadata in rules.items():
        if not isinstance(metadata, dict) or not isinstance(metadata.get("path"), str) or not isinstance(metadata.get("sha256"), str):
            errors.append(f"invalid Writing Check rule metadata: {name}")
            continue
        rel = metadata["path"]
        declared.add(rel)
        path = root / rel
        if not path.is_file():
            errors.append(f"missing Writing Check rule: {path.relative_to(ROOT)}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            errors.append(f"Writing Check rule digest mismatch: {path.relative_to(ROOT)}")
    actual = {path.relative_to(root).as_posix() for path in (root / "styles/GoogleDocs").glob("*.yml")}
    if actual != declared:
        errors.append("Writing Check rule inventory mismatch")


def main() -> int:
    errors: list[str] = []
    if "--plugin" in sys.argv:
        index = sys.argv.index("--plugin")
        if index + 1 == len(sys.argv):
            print("--plugin requires a path")
            return 2
        validate_plugin(pathlib.Path(sys.argv[index + 1]).resolve(), errors)
        print("\n".join(errors) if errors else "plugin validation passed")
        return int(bool(errors))
    try:
        inventory = json.loads((ROOT / "provenance.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid provenance: {error}")
        return 1
    for key in ("schema", "source_revision", "decision", "entries", "excluded"):
        if not inventory.get(key): errors.append(f"provenance missing {key}")
    entries = inventory.get("entries", [])
    for entry in entries:
        if not entry.get("origin") or not entry.get("license"): errors.append(f"provenance entry lacks origin/license: {entry}")
    for path in shipped():
        rel = path.relative_to(ROOT).as_posix()
        if not covered(rel, entries): errors.append(f"provenance missing shipped path: {rel}")
        if path.suffix in TEXT and rel not in {"provenance.json", "scripts/validate.py"} and not rel.startswith("tests/"):
            for token in PRIVATE:
                if re.search(token, path.read_text(encoding="utf-8"), re.I): errors.append(f"{rel}: private token {token}")
    for base in (ROOT / "plugins/context-engineering/skills", ROOT / "skills/writing"):
        for path in base.glob("*/SKILL.md"):
            match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: .+\n---\n", path.read_text(), re.S)
            if not match or match.group(1) != path.parent.name: errors.append(f"{path.relative_to(ROOT)}: invalid metadata")
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORED for part in path.parts): continue
        for link in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", path.read_text()):
            if "://" not in link and not (path.parent / link).exists(): errors.append(f"{path.relative_to(ROOT)}: missing {link}")
    validate_writing_policy(errors)
    validate_plugin(ROOT / "plugins/context-engineering", errors)
    if "--copied" not in sys.argv:
        with tempfile.TemporaryDirectory() as temp:
            artifact = pathlib.Path(temp) / "artifact"
            shutil.copytree(ROOT, artifact, ignore=shutil.ignore_patterns(".git", *IGNORED - {".git"}))
            result = subprocess.run([sys.executable, str(artifact / "scripts/validate.py"), "--copied"], capture_output=True, text=True)
            if result.returncode: errors.append("copied artifact validation failed: " + result.stdout + result.stderr)
    print("\n".join(errors) if errors else "validation passed")
    return int(bool(errors))


if __name__ == "__main__": raise SystemExit(main())
