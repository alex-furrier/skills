import importlib.util
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

ROOT = pathlib.Path(__file__).parents[1]
CONTEXT = ROOT / "packages/context-engineering"
WRITING = ROOT / "packages/writing-check"
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
    assert "context_engineering_cli-2.6.1.dist-info/licenses/LICENSE" in names
    assert "provenance.json" in names
    environment = tmp_path / "venv"
    assert run("uv", "venv", str(environment)).returncode == 0
    assert run("uv", "pip", "install", "--python", str(environment / "bin/python"), str(wheel)).returncode == 0
    command = str(environment / "bin/context-engineering")
    assert run(command, "--help").returncode == 0
    result = run(command, "references", ".", "--json")
    assert result.returncode == 0 and result.stdout.startswith("{")


@pytest.mark.parametrize(
    ("package", "command", "expected_files", "distribution"),
    [
        (CONTEXT, "context-engineering", {"context_engineering/cli/dispatch.py"}, "context_engineering_cli-2.6.1"),
        (WRITING, "writing-check", {
            "writing_check/cli.py", "writing_check/sweep.py", "writing_check/vale/.vale.ini",
            "writing_check/vale/profiles.json", "writing_check/vale/upstream-lock.json",
            "writing_check/vale/vendor/Google-LICENSE",
        }, "writing_check_cli-1.0.1"),
    ],
)
def test_independent_wheel_install_from_unrelated_directory(
    tmp_path, package, command, expected_files, distribution
):
    dist = tmp_path / "dist"
    built = run("uv", "build", str(package), "--out-dir", str(dist), cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata = archive.read(f"{distribution}.dist-info/METADATA").decode()
    assert expected_files | {"provenance.json", f"{distribution}.dist-info/licenses/LICENSE"} <= names
    assert ("Requires-Dist: vale==3.21.0.0" in metadata) == (command == "writing-check")
    environment = tmp_path / "venv"
    assert run("uv", "venv", str(environment), cwd=tmp_path).returncode == 0
    installed = run("uv", "pip", "install", "--python", str(environment / "bin/python"), str(wheel), cwd=tmp_path)
    assert installed.returncode == 0, installed.stderr
    binary = str(environment / "bin" / command)
    assert run(binary, "--help", cwd=tmp_path).returncode == 0
    if command == "writing-check":
        candidate = tmp_path / "candidate.md"
        candidate.write_text("A short candidate.\n", encoding="utf-8")
        local_vale = environment / "bin/vale"
        assert local_vale.is_file()  # The pinned dependency installed beside the CLI, not globally.
        hidden_vale = environment / "bin/vale-hidden"
        local_vale.rename(hidden_vale)  # Do not trigger the wrapper's first-use network download.
        checked = subprocess.run(
            [binary, "--profile", "commit", "--json", str(candidate)],
            cwd=tmp_path, text=True, capture_output=True, env={"PATH": ""},
        )
        record = json.loads(checked.stdout)
        assert checked.returncode == 3, checked.stderr
        assert record["status"] == record["vale"]["status"] == "unavailable"
        assert record["source"]["sha256"] == hashlib.sha256(candidate.read_bytes()).hexdigest()
    else:
        checked = run(binary, "references", ".", "--json", cwd=tmp_path)
        assert checked.returncode == 0 and checked.stdout.startswith("{"), checked.stderr


def test_release_workflows_pin_full_setup_uv_sha_and_guard_context_recovery():
    context = (ROOT / ".github/workflows/publish-context-engineering.yml").read_text()
    writing = (ROOT / ".github/workflows/publish-writing-check.yml").read_text()
    pin = "astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e"
    assert pin in context and pin in writing
    assert "workflow_dispatch:" in context
    assert "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.tag || github.event.release.tag_name }}" in context
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"' in context
    assert 'release["tag_name"] != os.environ["RELEASE_TAG"]' in context
    assert 'context-engineering "refs/tags/$RELEASE_TAG" "$RELEASE_TAG" --dist dist' in context
    assert 'release["draft"] or release["prerelease"]' in context
    assert '"refs/tags/$RELEASE_TAG" "$RELEASE_TAG"' in context


def test_release_validation_passes():
    result = run(sys.executable, "scripts/validate.py")
    assert result.returncode == 0, result.stdout


def test_docs_recommend_published_registry_installs_with_source_fallback():
    readme = (ROOT / "README.md").read_text()
    installation = (ROOT / "docs/installation.md").read_text()
    publishing = (ROOT / "docs/publishing.md").read_text()
    for text in (readme, installation):
        assert "uv tool install context-engineering-cli==2.6.1" in text
        assert "context-engineering-cli==2.6.0" not in text
        assert "uv tool install writing-check-cli==1.0.1" in text
        assert "explicit" in text and "consent" in text
        assert "writing-check --help" in text
        assert "runtime install" not in text and "writing-check doctor" not in text
    assert "Writing and Writing Check are one suite" in installation
    assert "optional suite" in installation
    assert 'uv tool install "$checkout/skills/packages/context-engineering"' in installation
    assert 'uv tool install "$checkout/skills/packages/writing-check"' in installation
    assert "gh repo clone alex-furrier/skills" in installation
    assert "private" in installation and "authenticated" in installation
    assert "published Context Engineering CLI 2.6.1" in installation
    assert "https://pypi.org/project/context-engineering-cli/" in installation
    assert "https://pypi.org/project/context-engineering-cli/2.6.1/" in publishing
    assert "context-engineering-v2.6.1" in publishing
    assert "fda3af779a399f7b3b5f586e7dcf119d2be3638c" in publishing
    assert "https://github.com/alex-furrier/skills/actions/runs/36173696116" in publishing
    assert "context-engineering-v2.6.0" in publishing
    assert "https://pypi.org/project/writing-check-cli/" in installation
    assert "https://github.com/alex-furrier/skills/actions/runs/36072208510" in publishing
    assert "https://github.com/alex-furrier/skills/actions/runs/36072533222" in publishing


def test_all_canonical_cli_skills_pin_registry_installs():
    for directory, package, version in (
        ("context-engineering", "context-engineering-cli", "2.6.1"),
        ("writing", "writing-check-cli", "1.0.1"),
    ):
        for skill in (ROOT / "skills" / directory).glob("*/SKILL.md"):
            text = skill.read_text()
            if f"uv tool install {package}" in text:
                assert f"uv tool install {package}=={version}" in text, skill
                assert not re.search(rf"uv tool install {package}(?!=={re.escape(version)})", text), skill
                if directory == "context-engineering":
                    projected = PLUGIN / "skills" / skill.parent.name / "SKILL.md"
                    assert projected.read_text() == text


@pytest.mark.parametrize(
    ("skill", "package", "command", "version"),
    [("context-engineering/context-review", "context-engineering", "context-engineering", "2.6.1"),
     ("writing/writing-check", "writing-check", "writing-check", "1.0.1")],
)
def test_selected_skill_alone_documents_registry_and_optional_source_route(tmp_path, skill, package, command, version):
    copied = tmp_path / "selected-skill"
    shutil.copytree(ROOT / "skills" / skill, copied)
    text = (copied / "SKILL.md").read_text()
    assert f"uv tool install {package}-cli=={version}" in text
    assert "gh repo clone alex-furrier/skills" in text
    assert f'uv tool install "$checkout/skills/packages/{package}"' in text
    assert f"{command} --help" in text
    assert "consent" in text and "private" in text and "unavailable" in text
    assert text.index(f"uv tool install {package}-cli=={version}") < text.index("gh repo clone")
    assert not (tmp_path / "packages").exists()


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
