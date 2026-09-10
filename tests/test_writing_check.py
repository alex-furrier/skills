import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parents[1]


def copied_skill(tmp_path):
    skill = tmp_path / "arbitrary" / "writing-check"
    skill.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/writing/writing-check", skill)
    return skill


def fake_vale(tmp_path, lint_stdout="{}", lint_exit=0, version_stdout="vale version 3.0", version_stderr="", version_exit=0):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    script = bin_dir / "vale"
    version_stdout_bytes = version_stdout.encode() if isinstance(version_stdout, str) else version_stdout
    version_stderr_bytes = version_stderr.encode() if isinstance(version_stderr, str) else version_stderr
    script.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, sys\n"
        "capture = pathlib.Path(__file__).with_name('captured-stdin')\n"
        "if sys.argv[1:] == ['--version']:\n"
        f"    sys.stdout.buffer.write({version_stdout_bytes!r})\n"
        f"    sys.stderr.buffer.write({version_stderr_bytes!r})\n"
        f"    raise SystemExit({version_exit})\n"
        "capture.write_bytes(sys.stdin.buffer.read())\n"
        f"sys.stdout.write({lint_stdout!r})\n"
        f"raise SystemExit({lint_exit})\n"
    )
    script.chmod(0o755)
    return bin_dir


def check(skill, profile, input_path, env):
    return subprocess.run(
        [sys.executable, str(skill / "scripts/writing_check.py"), "--profile", profile, "--json", input_path],
        text=True, input=None, capture_output=True, env=env,
    )


def test_writing_check_stdin_lints_the_retained_source_bytes(tmp_path):
    skill = copied_skill(tmp_path)
    bin_dir = fake_vale(tmp_path)
    source = b"Exact candidate: caf\xc3\xa9.\n"
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/writing_check.py"), "--profile", "commit", "--json", "-"],
        input=source, capture_output=True, env={"PATH": str(bin_dir)},
    )
    data = json.loads(result.stdout)
    assert result.returncode == 0
    assert (bin_dir / "captured-stdin").read_bytes() == source
    assert data["source"]["sha256"] == hashlib.sha256(source).hexdigest()
    assert data["source"]["bytes"] == len(source)
    assert data["vale"]["lint"]["argv"][-1] == "-"
    assert "--ext=.md" in data["vale"]["lint"]["argv"]
    assert "--no-global" in data["vale"]["lint"]["argv"]


def test_writing_check_version_failure_is_execution_error_with_evidence(tmp_path):
    skill = copied_skill(tmp_path)
    bin_dir = fake_vale(tmp_path, version_stdout="bad version", version_exit=2)
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
    data = json.loads(result.stdout)
    assert result.returncode == 4 and data["status"] == "execution_error"
    assert data["vale"]["version"] == {"argv": [str(bin_dir / "vale"), "--version"], "exit": 2, "stdout": "bad version", "stderr": ""}


def test_writing_check_rejects_invalid_utf8_version_output_with_evidence(tmp_path):
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    for index, (version_stdout, version_stderr) in enumerate(((b"vale \xff", b""), (b"vale version 3.0", b"warning \xff"))):
        skill = copied_skill(tmp_path / f"skill-{index}")
        bin_dir = fake_vale(tmp_path / f"fake-{index}", version_stdout=version_stdout, version_stderr=version_stderr)
        result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
        data = json.loads(result.stdout)
        assert result.returncode == 4 and data["status"] == "execution_error"
        assert data["vale"]["version"] == {
            "argv": [str(bin_dir / "vale"), "--version"],
            "exit": 0,
            "stdout": version_stdout.decode("utf-8", errors="replace"),
            "stderr": version_stderr.decode("utf-8", errors="replace"),
        }


def test_writing_check_rejects_unsupported_lint_exit_with_evidence(tmp_path):
    skill = copied_skill(tmp_path)
    bin_dir = fake_vale(tmp_path, lint_stdout="not-json", lint_exit=2)
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
    data = json.loads(result.stdout)
    assert result.returncode == 4 and data["status"] == "execution_error"
    assert data["vale"]["lint"]["exit"] == 2
    assert data["vale"]["lint"]["stdout"] == "not-json"


def test_writing_check_rejects_invalid_vale_json_and_root_shape(tmp_path):
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    for output in ("not-json", "{\"candidate.md\": {\"Check\": \"GoogleDocs.AMPM\"}}", "42"):
        skill = copied_skill(tmp_path / hashlib.sha256(output.encode()).hexdigest())
        bin_dir = fake_vale(tmp_path / ("bin-" + hashlib.sha256(output.encode()).hexdigest()), lint_stdout=output)
        result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
        data = json.loads(result.stdout)
        assert result.returncode == 4 and data["status"] == "execution_error"
        assert data["vale"]["lint"]["stdout"] == output


def test_writing_check_rejects_malformed_alerts_and_coordinates(tmp_path):
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    cases = [
        {"candidate.md": [{"Message": "missing check", "Line": 1, "Span": [1, 2]}]},
        {"candidate.md": [{"Check": "GoogleDocs.AMPM", "Message": "missing line", "Span": [1, 2]}]},
        {"candidate.md": [{"Check": "GoogleDocs.AMPM", "Message": "bad span", "Line": 0, "Span": [1, 2]}]},
        {"candidate.md": [{"Check": "GoogleDocs.AMPM", "Message": "bad span", "Line": 1, "Span": [0, 2]}]},
    ]
    for index, document in enumerate(cases):
        skill = copied_skill(tmp_path / f"skill-{index}")
        bin_dir = fake_vale(tmp_path / f"fake-{index}", lint_stdout=json.dumps(document))
        result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
        assert result.returncode == 4
        assert json.loads(result.stdout)["status"] == "execution_error"


def test_writing_check_rejects_tampered_or_missing_policy_content(tmp_path):
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    for index, mutation in enumerate(("tamper-rule", "remove-rule", "tamper-license", "remove-config")):
        skill = copied_skill(tmp_path / f"skill-{index}")
        if mutation == "tamper-rule":
            rule = skill / "vale/styles/GoogleDocs/AMPM.yml"
            rule.write_text(rule.read_text() + "\n# tampered\n")
        elif mutation == "remove-rule":
            (skill / "vale/styles/GoogleDocs/AMPM.yml").unlink()
        elif mutation == "tamper-license":
            license_file = skill / "vale/vendor/Google-LICENSE"
            license_file.write_text(license_file.read_text() + "\ntampered\n")
        else:
            (skill / "vale/.vale.ini").unlink()
        bin_dir = fake_vale(tmp_path / f"fake-{index}")
        result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
        data = json.loads(result.stdout)
        assert result.returncode == 4 and data["status"] == "execution_error"
        assert data["error"]["code"] == "policy_validation_failed"


def test_writing_check_valid_alerts_are_normalized_as_suggestions(tmp_path):
    skill = copied_skill(tmp_path)
    document = {"candidate.md": [{"Check": "GoogleDocs.AMPM", "Message": "Use a.m.", "Line": 2, "Span": [1, 4]}]}
    bin_dir = fake_vale(tmp_path, lint_stdout=json.dumps(document))
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
    data = json.loads(result.stdout)
    assert result.returncode == 1 and data["alerts"] == [{"source": "vale", "rule": "GoogleDocs.AMPM", "message": "Use a.m.", "severity": "suggestion", "line": 2, "span": [1, 4], "path": "candidate.md"}]
