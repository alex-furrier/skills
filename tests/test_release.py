import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).parents[1]
CONTEXT = ROOT / "packages/context-engineering"
PLUGIN = ROOT / "plugins/context-engineering"


def projection_module():
    spec = importlib.util.spec_from_file_location("project_context_plugin", ROOT / "scripts/project_context_plugin.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True)


def test_all_canonical_skills_have_valid_metadata_and_resolving_links(tmp_path):
    copied = tmp_path / "arbitrary" / "skills"
    copied.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills", copied)
    skills = list(copied.glob("*/*/SKILL.md"))
    assert skills
    for skill in skills:
        match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: .+\n---", skill.read_text(), re.S)
        assert match and match.group(1) == skill.parent.name
    for path in copied.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text()):
            if "://" not in target:
                assert (path.parent / target).exists(), (path, target)


def test_claude_plugin_is_exact_projection_of_canonical_context_sources():
    result = run(sys.executable, "scripts/project_context_plugin.py", "--check")
    assert result.returncode == 0, result.stdout


def test_projection_comparison_checks_common_files_by_bytes_when_metadata_matches(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    source_file = source / "same-size.txt"
    destination_file = destination / "same-size.txt"
    source_file.write_text("source", encoding="utf-8")
    destination_file.write_text("target", encoding="utf-8")
    timestamp = 1_700_000_000_000_000_000
    os.utime(source_file, ns=(timestamp, timestamp))
    os.utime(destination_file, ns=(timestamp, timestamp))
    assert source_file.stat().st_size == destination_file.stat().st_size
    assert source_file.stat().st_mtime_ns == destination_file.stat().st_mtime_ns
    assert not projection_module().same_tree(source, destination)


def test_context_wheel_contains_cli_and_installs_from_an_arbitrary_path(tmp_path):
    dist = tmp_path / "dist"
    result = run("uv", "build", str(CONTEXT), "--out-dir", str(dist))
    assert result.returncode == 0, result.stderr
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "context_engineering/cli/dispatch.py" in names
    assert "safurrier_context_engineering-2.6.0.dist-info/licenses/LICENSE" in names
    assert "provenance.json" in names
    environment = tmp_path / "venv"
    assert run("uv", "venv", str(environment)).returncode == 0
    assert run("uv", "pip", "install", "--python", str(environment / "bin/python"), str(wheel)).returncode == 0
    command = str(environment / "bin/context-engineering")
    assert run(command, "--help").returncode == 0
    result = run(command, "references", ".", "--json")
    assert result.returncode == 0 and result.stdout.startswith("{")


def test_release_validation_passes():
    result = run(sys.executable, "scripts/validate.py")
    assert result.returncode == 0, result.stdout


def test_docs_describe_source_installs_and_defer_registry_commands_until_publication():
    text = "\n".join((ROOT / name).read_text() for name in ("README.md", "docs/installation.md"))
    assert "Writing and Writing Check are one suite" in text
    assert "optional suite" in text
    assert "uv tool install ./packages/context-engineering" in text
    assert "uv tool install ./packages/writing-check" in text
    assert "After package publication" in text
    assert "writing-check --help" in text
    assert "runtime install" not in text and "writing-check doctor" not in text


def test_docs_verifier_uses_installed_context_command_from_a_copied_skill(tmp_path):
    dist = tmp_path / "dist"
    assert run("uv", "build", str(CONTEXT), "--out-dir", str(dist)).returncode == 0
    environment = tmp_path / "venv"
    assert run("uv", "venv", str(environment)).returncode == 0
    wheel = next(dist.glob("*.whl"))
    assert run("uv", "pip", "install", "--python", str(environment / "bin/python"), str(wheel)).returncode == 0
    skill = tmp_path / "copied-skill"
    shutil.copytree(ROOT / "skills/context-engineering/context-docs", skill)
    env = {"PATH": f"{environment / 'bin'}:{os.environ['PATH']}"}
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/docs_verify.py"), str(ROOT)],
        text=True,
        capture_output=True,
        env=env,
    )
    record = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert record["context_cli"] == "available"
    assert set(record["checks"]) == {"frontmatter", "references"}


def test_docs_verifier_reports_unexecutable_context_command_as_evidence(tmp_path):
    skill = tmp_path / "copied-skill"
    shutil.copytree(ROOT / "skills/context-engineering/context-docs", skill)
    commands = tmp_path / "commands"
    commands.mkdir()
    command = commands / "context-engineering"
    command.write_text("not an executable\n", encoding="utf-8")
    command.chmod(0o644)
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/docs_verify.py"), str(ROOT)],
        text=True,
        capture_output=True,
        env={"PATH": str(commands)},
    )
    record = json.loads(result.stdout)
    assert result.returncode == 4
    assert record["context_cli"] == "execution_error"
    assert "could not be executed" in record["reason"]
    assert record["findings"] == []


def test_fast_check_runs_writing_check_on_the_exact_readme_candidate():
    text = (ROOT / "scripts/fast_check.py").read_text()
    assert '"packages/writing-check"' in text
    assert '"--profile",' in text and '"readme",' in text
    assert '"README.md",' in text
    assert "allowed_returncodes=(0, 1)" in text
