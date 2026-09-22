import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).parents[1]
CONTEXT = ROOT / "packages/context-engineering"
PLUGIN = ROOT / "plugins/context-engineering"


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


def test_context_wheel_contains_cli_and_installs_from_an_arbitrary_path(tmp_path):
    dist = tmp_path / "dist"
    result = run("uv", "build", str(CONTEXT), "--out-dir", str(dist))
    assert result.returncode == 0, result.stderr
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert "context_engineering/cli/dispatch.py" in archive.namelist()
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


def test_docs_describe_independent_commands_without_a_second_vale_setup():
    text = "\n".join((ROOT / name).read_text() for name in ("README.md", "docs/installation.md"))
    assert "uv tool install safurrier-context-engineering" in text
    assert "uv tool install safurrier-writing-check" in text
    assert "writing-check --help" in text
    assert "runtime install" not in text and "writing-check doctor" not in text
