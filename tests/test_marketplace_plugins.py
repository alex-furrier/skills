"""Marketplace artifacts must survive copying without the catalog checkout."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from project_review_plugins import build  # noqa: E402
from project_thinking_plugin import check  # noqa: E402


@pytest.mark.parametrize("suite", ["code-quality", "writing"])
def test_independently_copied_plugin(tmp_path: Path, suite: str) -> None:
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(item for item in marketplace["plugins"] if item["name"] == suite)
    copied = tmp_path / suite
    shutil.copytree(ROOT / entry["source"], copied)
    expected = build(ROOT, suite)
    assert check(expected, copied)
    metadata = json.loads((copied / ".claude-plugin/plugin.json").read_text())
    assert metadata["name"] == suite
    assert set(metadata["skills"]) == {
        f"./skills/{path.name}" for path in (ROOT / "skills" / suite).iterdir() if path.is_dir()
    }
    for skill in metadata["skills"]:
        assert (copied / skill / "SKILL.md").is_file()
    # Both changed and unexpected bytes must invalidate the checked projection.
    (copied / "unexpected.txt").write_text("stale")
    assert not check(expected, copied)
    (copied / "unexpected.txt").unlink()
    (copied / metadata["skills"][0] / "SKILL.md").write_text("drift")
    assert not check(expected, copied)


def test_local_artifacts_are_not_shipped(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "skills/writing", tmp_path / "skills/writing")
    shutil.copy2(ROOT / "LICENSE", tmp_path / "LICENSE")
    expected = build(tmp_path, "writing")
    source = tmp_path / "skills/writing"
    for relative in (
        "pr-description/scripts/__pycache__/helper.cpython-311.pyc",
        "pr-description/scripts/helper.pyc",
        "pr-description/.venv/lib/site-packages/example.py",
        "pr-description/venv/lib/site-packages/example.py",
        "pr-description/.pytest_cache/v/cache/nodeids",
        "pr-description/.mypy_cache/cache.json",
        "pr-description/.ruff_cache/cache.bin",
        "pr-description/node_modules/example/index.js",
        "pr-description/.DS_Store",
        ".pytest_cache/README.md",
        ".venv/lib/site-packages/example.py",
    ):
        artifact = source / relative
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"local artifact")
    assert build(tmp_path, "writing") == expected


def test_regeneration_check() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/project_review_plugins.py"), "--check"],
        cwd=ROOT, check=True,
    )


def test_copied_code_health_retains_checkout_fallback() -> None:
    skill = (ROOT / "plugins/code-quality/skills/code-health-review/SKILL.md").read_text()
    assert '$CATALOG/packages/code-health' in skill
    assert "git clone https://github.com/alex-furrier/skills" in skill
    assert "continue the qualitative review" in skill
