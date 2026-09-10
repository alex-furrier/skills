import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

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
        "    count = pathlib.Path(__file__).with_name('version-count')\n"
        "    count.write_text(str(int(count.read_text()) + 1) if count.exists() else '1')\n"
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


def checker_module():
    spec = importlib.util.spec_from_file_location("writing_check_test_module", ROOT / "skills/writing/writing-check/scripts/writing_check.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sweep_module():
    spec = importlib.util.spec_from_file_location("repository_sweep_check_test_module", ROOT / "skills/writing/writing-check/scripts/repository_sweep_check.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    for index, mutation in enumerate(("tamper-rule", "remove-rule", "tamper-license", "tamper-config", "remove-config")):
        skill = copied_skill(tmp_path / f"skill-{index}")
        if mutation == "tamper-rule":
            rule = skill / "vale/styles/GoogleDocs/AMPM.yml"
            rule.write_text(rule.read_text() + "\n# tampered\n")
        elif mutation == "remove-rule":
            (skill / "vale/styles/GoogleDocs/AMPM.yml").unlink()
        elif mutation == "tamper-license":
            license_file = skill / "vale/vendor/Google-LICENSE"
            license_file.write_text(license_file.read_text() + "\ntampered\n")
        elif mutation == "tamper-config":
            config = skill / "vale/.vale.ini"
            config.write_text(config.read_text().replace("MinAlertLevel = suggestion", "MinAlertLevel = error"))
        else:
            (skill / "vale/.vale.ini").unlink()
        bin_dir = fake_vale(tmp_path / f"fake-{index}")
        result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
        data = json.loads(result.stdout)
        assert result.returncode == 4 and data["status"] == "execution_error"
        assert data["error"]["code"] == "policy_validation_failed"
        assert "vale" not in data


def test_writing_check_rejects_non_object_upstream_lock_as_policy_error(tmp_path):
    skill = copied_skill(tmp_path)
    (skill / "vale/upstream-lock.json").write_text("[]")
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    result = check(skill, "commit", str(source), {"PATH": ""})
    data = json.loads(result.stdout)
    assert result.returncode == 4 and data["status"] == "execution_error"
    assert data["error"]["code"] == "policy_validation_failed"
    assert "invalid root" in data["error"]["message"]
    assert "vale" not in data


def test_writing_check_retains_lint_argv_when_lint_cannot_start(tmp_path, monkeypatch, capsys):
    checker = checker_module()
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")

    def fake_run(argv, **kwargs):
        if argv[-1] == "--version":
            return subprocess.CompletedProcess(argv, 0, b"vale version 3.0", b"")
        raise OSError("lint could not start")

    monkeypatch.setattr(checker.shutil, "which", lambda _: "/fake/vale")
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["writing_check.py", "--profile", "commit", "--json", str(source)])
    assert checker.main() == 4
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "execution_error"
    assert data["vale"]["version"]["argv"] == ["/fake/vale", "--version"]
    assert data["vale"]["lint"]["argv"][-1] == "-"


def test_writing_check_retains_timeout_partial_version_output(tmp_path, monkeypatch, capsys):
    checker = checker_module()
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")

    def fake_run(argv, **kwargs):
        assert argv == ["/fake/vale", "--version"]
        raise subprocess.TimeoutExpired(argv, 30, output=b"partial version \xff", stderr=b"partial stderr \xff")

    monkeypatch.setattr(checker.shutil, "which", lambda _: "/fake/vale")
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["writing_check.py", "--profile", "commit", "--json", str(source)])
    assert checker.main() == 4
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "execution_error"
    assert data["vale"]["version"] == {
        "argv": ["/fake/vale", "--version"],
        "stdout": "partial version \ufffd",
        "stderr": "partial stderr \ufffd",
    }


def test_writing_check_retains_timeout_partial_lint_output(tmp_path, monkeypatch, capsys):
    checker = checker_module()
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")

    def fake_run(argv, **kwargs):
        if argv[-1] == "--version":
            return subprocess.CompletedProcess(argv, 0, b"vale version 3.0", b"")
        raise subprocess.TimeoutExpired(argv, 30, output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(checker.shutil, "which", lambda _: "/fake/vale")
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["writing_check.py", "--profile", "commit", "--json", str(source)])
    assert checker.main() == 4
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "execution_error"
    assert data["vale"]["version"]["argv"] == ["/fake/vale", "--version"]
    assert data["vale"]["lint"]["argv"][-1] == "-"
    assert data["vale"]["lint"]["stdout"] == "partial stdout"
    assert data["vale"]["lint"]["stderr"] == "partial stderr"


def test_repository_sweep_check_emits_independent_records_and_shares_vale_probe(tmp_path):
    skill = copied_skill(tmp_path / "skill")
    bin_dir = fake_vale(tmp_path / "fake")
    first = tmp_path / "first.md"; first.write_text("First candidate.")
    second = tmp_path / "second.md"; second.write_text("Second candidate.")
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps([
        {"source": str(first), "profile": "commit"},
        {"source": str(second), "profile": "commit"},
    ]))
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/repository_sweep_check.py"), "--candidates", str(candidates), "--jsonl"],
        text=True, capture_output=True, env={"PATH": str(bin_dir)},
    )
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert result.returncode == 0
    assert [record["schema"] for record in records] == [3, 3]
    assert [record["status"] for record in records] == ["no_findings", "no_findings"]
    assert [record["source"]["sha256"] for record in records] == [
        hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest()
    ]
    assert (bin_dir / "version-count").read_text() == "1"


def test_repository_sweep_check_replays_probe_failures_as_independent_evidence(tmp_path, monkeypatch):
    checker = checker_module()
    sweep = sweep_module()
    first = tmp_path / "first.md"; first.write_text("First candidate.")
    second = tmp_path / "second.md"; second.write_text("Second candidate.")
    calls = 0

    def fake_run(argv, **kwargs):
        nonlocal calls
        calls += 1
        raise OSError("Vale could not start")

    monkeypatch.setattr(sweep, "_load_checker", lambda: checker)
    monkeypatch.setattr(checker.shutil, "which", lambda _: "/fake/vale")
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    records, code = sweep.run([(str(first), "commit"), (str(second), "commit")])
    assert calls == 1
    assert code == 4
    assert [record["status"] for record in records] == ["execution_error", "execution_error"]
    assert [record["vale"]["error"] for record in records] == ["Vale could not start", "Vale could not start"]


@pytest.mark.parametrize("probe_error", [KeyboardInterrupt(), SystemExit()])
def test_repository_sweep_check_does_not_swallow_process_control_exceptions(tmp_path, monkeypatch, probe_error):
    checker = checker_module()
    sweep = sweep_module()
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")

    def fake_run(argv, **kwargs):
        raise probe_error

    monkeypatch.setattr(sweep, "_load_checker", lambda: checker)
    monkeypatch.setattr(checker.shutil, "which", lambda _: "/fake/vale")
    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    with pytest.raises(type(probe_error)):
        sweep.run([(str(source), "commit")])


def test_repository_sweep_check_preserves_per_candidate_failure_status(tmp_path):
    skill = copied_skill(tmp_path / "skill")
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps([{"source": str(source), "profile": "not-a-profile"}]))
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/repository_sweep_check.py"), "--candidates", str(candidates), "--jsonl"],
        text=True, capture_output=True, env={"PATH": ""},
    )
    record = json.loads(result.stdout)
    assert result.returncode == 2
    assert record["schema"] == 3 and record["status"] == "input_error"
    assert record["error"]["code"] == "unknown_profile"


def test_repository_sweep_check_accepts_dash_prefixed_source_name(tmp_path):
    skill = copied_skill(tmp_path / "skill")
    bin_dir = fake_vale(tmp_path / "fake")
    (tmp_path / "--help").write_text("Candidate.")
    candidates = tmp_path / "candidates.json"
    candidates.write_text(json.dumps([{"source": "--help", "profile": "commit"}]))
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/repository_sweep_check.py"), "--candidates", str(candidates), "--jsonl"],
        text=True, capture_output=True, cwd=tmp_path, env={"PATH": str(bin_dir)},
    )
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert result.returncode == 0
    assert len(records) == 1
    assert records[0]["schema"] == 3 and records[0]["status"] == "no_findings"


def test_writing_check_valid_alerts_are_normalized_as_suggestions(tmp_path):
    skill = copied_skill(tmp_path)
    document = {"candidate.md": [{"Check": "GoogleDocs.AMPM", "Message": "Use a.m.", "Line": 2, "Span": [1, 4]}]}
    bin_dir = fake_vale(tmp_path, lint_stdout=json.dumps(document))
    source = tmp_path / "candidate.md"; source.write_text("Candidate.")
    result = check(skill, "commit", str(source), {"PATH": str(bin_dir)})
    data = json.loads(result.stdout)
    assert result.returncode == 1 and data["alerts"] == [{"source": "vale", "rule": "GoogleDocs.AMPM", "message": "Use a.m.", "severity": "suggestion", "line": 2, "span": [1, 4], "path": "candidate.md"}]
