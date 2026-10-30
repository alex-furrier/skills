"""Prove distribution ownership and portability without a source Dots checkout."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location(
        "thinking_projection", ROOT / "scripts/project_thinking_plugin.py"
    )
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_projection_is_current_and_contains_only_three_independent_skills():
    projector = module()
    plugin = ROOT / "plugins/thinking"
    assert projector.check(projector.build(ROOT), plugin)
    metadata = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
    assert metadata["name"] == "thinking"
    assert metadata["skills"] == [
        "./skills/blindspot",
        "./skills/research",
        "./skills/goalify",
    ]
    assert {p.name for p in (plugin / "skills").iterdir()} == {
        "blindspot",
        "research",
        "goalify",
    }
    assert (ROOT / "skills/product/product-bet-shaping/SKILL.md").is_file()


def test_independent_copied_artifacts_have_complete_local_resources_and_legal_context(
    tmp_path,
):
    artifacts = [
        ROOT / "plugins/thinking",
        *sorted((ROOT / "skills/thinking").iterdir()),
        ROOT / "skills/product/product-bet-shaping",
    ]
    for index, source in enumerate(artifacts):
        copied = tmp_path / str(index)
        shutil.copytree(source, copied)
        assert (copied / "LICENSE").is_file()
        provenance = json.loads((copied / "provenance.json").read_text())
        for path in copied.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(copied).as_posix()
            assert any(
                relative == entry.get("path")
                or relative.startswith(entry.get("path_prefix", "\0"))
                for entry in provenance["entries"]
            ), relative
            if path.suffix == ".md":
                for link in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text()):
                    if "://" not in link:
                        assert (path.parent / link).is_file(), (path, link)
        for skill in copied.rglob("SKILL.md"):
            frontmatter = skill.read_text().split("---")[1]
            assert set(re.findall(r"^(\w[\w-]*):", frontmatter, re.MULTILINE)) == {
                "name",
                "description",
            }
        assert not any(
            p.name in {"evals", "cli", "packages"} for p in copied.rglob("*")
        )


def test_check_rejects_modified_or_added_plugin_payload_and_missing_reference(tmp_path):
    projector = module()
    copied = tmp_path / "thinking"
    shutil.copytree(ROOT / "plugins/thinking", copied)
    files = projector.build(ROOT)
    (copied / "skills/research/references/anti-hallucination.md").unlink()
    assert not projector.check(files, copied)
    shutil.copyfile(
        ROOT / "plugins/thinking/skills/research/references/anti-hallucination.md",
        copied / "skills/research/references/anti-hallucination.md",
    )
    assert projector.check(files, copied)
    (copied / "skills/research/SKILL.md").write_text("modified")
    assert not projector.check(files, copied)
    (copied / "unexpected.txt").write_text("extra")
    assert not projector.check(files, copied)


def test_projection_runs_from_independent_checkout(tmp_path):
    # Carry only this catalog's source closure and generator; no checkout imports.
    shutil.copytree(ROOT / "skills/thinking", tmp_path / "skills/thinking")
    shutil.copyfile(ROOT / "LICENSE", tmp_path / "LICENSE")
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(
        ROOT / "scripts/project_thinking_plugin.py",
        tmp_path / "scripts/project_thinking_plugin.py",
    )
    for arguments in ([], ["--check"]):
        result = subprocess.run(
            [sys.executable, "scripts/project_thinking_plugin.py", *arguments],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_projection_refuses_symlinked_destination_root(tmp_path):
    projector = module()
    copied = tmp_path / "target"
    shutil.copytree(ROOT / "plugins/thinking", copied)
    linked = tmp_path / "linked"
    linked.symlink_to(copied, target_is_directory=True)
    assert not projector.check(projector.build(ROOT), linked)
    isolated = tmp_path / "isolated"
    shutil.copytree(ROOT / "skills/thinking", isolated / "skills/thinking")
    shutil.copyfile(ROOT / "LICENSE", isolated / "LICENSE")
    (isolated / "scripts").mkdir()
    shutil.copyfile(
        ROOT / "scripts/project_thinking_plugin.py",
        isolated / "scripts/project_thinking_plugin.py",
    )
    (isolated / "plugins").mkdir()
    (isolated / "plugins/thinking").symlink_to(copied, target_is_directory=True)
    (copied / "README.md").write_text("human edit")
    result = subprocess.run(
        [sys.executable, "scripts/project_thinking_plugin.py"],
        cwd=isolated,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert (copied / "README.md").read_text() == "human edit"
