import json
import os
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).parents[1]
PACKAGE = ROOT / "packages/writing-check"


def test_writing_wheel_contains_cli_policy_and_license(tmp_path):
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(PACKAGE), "--out-dir", str(dist)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert {
        "writing_check/cli.py",
        "writing_check/sweep.py",
        "writing_check/vale/profiles.json",
        "writing_check/vale/vendor/Google-LICENSE",
        "provenance.json",
        "writing_check_cli-1.0.0.dist-info/licenses/LICENSE",
    } <= names


def install_wheel(tmp_path):
    dist = tmp_path / "dist"
    assert subprocess.run(["uv", "build", str(PACKAGE), "--out-dir", str(dist)]).returncode == 0
    environment = tmp_path / "venv"
    assert subprocess.run(["uv", "venv", str(environment)]).returncode == 0
    wheel = next(dist.glob("*.whl"))
    assert subprocess.run(["uv", "pip", "install", "--python", str(environment / "bin/python"), str(wheel)]).returncode == 0
    return environment


def test_documented_tool_install_finds_its_own_vale_dependency(tmp_path):
    tools, binaries = tmp_path / "tools", tmp_path / "bin"
    environment = {**os.environ, "UV_TOOL_DIR": str(tools), "UV_TOOL_BIN_DIR": str(binaries)}
    installed = subprocess.run(["uv", "tool", "install", "./packages/writing-check"], cwd=ROOT, text=True, capture_output=True, env=environment)
    assert installed.returncode == 0, installed.stderr
    candidate = tmp_path / "candidate.md"
    candidate.write_text("A short candidate.\n", encoding="utf-8")
    result = subprocess.run([str(binaries / "writing-check"), "--profile", "commit", "--json", str(candidate)], text=True, capture_output=True, env={"PATH": ""})
    record = json.loads(result.stdout)
    assert result.returncode in (0, 1)
    assert record["status"] in {"no_findings", "findings"}
    vale_path = pathlib.Path(record["vale"]["argv"][0])
    assert tools in vale_path.parents
    assert binaries not in vale_path.parents


def test_writing_wheel_installs_a_working_command_without_extra_setup(tmp_path):
    environment = install_wheel(tmp_path)
    help_result = subprocess.run([str(environment / "bin/writing-check"), "--help"], text=True, capture_output=True)
    assert help_result.returncode == 0 and "--profile" in help_result.stdout
    sample = tmp_path / "candidate.md"
    sample.write_text("A short candidate.\n", encoding="utf-8")
    result = subprocess.run([str(environment / "bin/writing-check"), "--profile", "commit", "--json", str(sample)], text=True, capture_output=True)
    record = json.loads(result.stdout)
    assert result.returncode in (0, 1)
    assert record["status"] in {"no_findings", "findings"}
    assert record["source"]["sha256"]


def test_writing_check_reports_missing_or_invalid_vale_as_evidence(tmp_path):
    environment = install_wheel(tmp_path)
    command = str(environment / "bin/writing-check")
    candidate = tmp_path / "candidate.md"
    candidate.write_text("Exact candidate.\n", encoding="utf-8")
    installed_vale = environment / "bin/vale"
    hidden_vale = environment / "bin/vale-hidden"
    installed_vale.rename(hidden_vale)
    unavailable = subprocess.run([command, "--profile", "commit", "--json", str(candidate)], text=True, capture_output=True, env={"PATH": ""})
    record = json.loads(unavailable.stdout)
    assert unavailable.returncode == 3 and record["status"] == "unavailable"
    fake = tmp_path / "fake"
    fake.mkdir()
    vale = fake / "vale"
    vale.write_text("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then exit 2; fi\n", encoding="utf-8")
    vale.chmod(0o755)
    invalid = subprocess.run([command, "--profile", "commit", "--json", str(candidate)], text=True, capture_output=True, env={"PATH": str(fake)})
    record = json.loads(invalid.stdout)
    assert invalid.returncode == 4 and record["status"] == "execution_error"
