from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).parents[1] / "evals" / "real_repository_validation.py"
spec = importlib.util.spec_from_file_location("real_repository_validation", HARNESS)
assert spec and spec.loader
validation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validation
spec.loader.exec_module(validation)


def report(case: object, mode: str) -> dict[str, object]:
    return {
        "status": "ok",
        "languages": [case.language],
        "tools": [
            {"tool": case.tool, "status": "ok", "detail": "pinned tool preparation"},
            {"tool": case.tool, "status": "ok", "detail": "pinned tool analysis"},
        ],
        "findings": [{"tool": case.tool, "path": "source", "rule": "complexity"}],
        "deltas": [] if mode == "scan" else [{"status": "unchanged"}],
    }


def test_harness_uses_full_pinned_revisions_and_requires_empty_workdir(tmp_path: Path) -> None:
    parser = validation.build_parser()
    arguments = parser.parse_args(["--workdir", str(tmp_path / "empty")])

    assert arguments.workdir == tmp_path / "empty"
    assert all(validation.REVISION.fullmatch(case.revision) for case in validation.CASES)
    assert validation.TYPESCRIPT_REPOSITORY.endswith("pi-sprite.git")
    assert validation.GO_REPOSITORY.endswith("ksuid.git")

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "leftover").write_text("x")
    assert validation.main(["--workdir", str(occupied)]) == 2


def test_harness_returns_observable_success_with_tool_provenance(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_case(case: object, _workdir: Path, _cli: Path) -> dict[str, object]:
        return {
            "repository": case.repository,
            "revision": case.revision,
            "reports": {
                mode: validation.validate_report(case, mode, report(case, mode))
                for mode in ("scan", "diff")
            },
        }

    monkeypatch.setattr(validation, "validate_case", fake_case)
    monkeypatch.setattr(validation, "pinned_golangci_version", lambda: validation.GOLANGCI_VERSION)
    cli = tmp_path / "cli"
    cli.mkdir()
    (cli / "pyproject.toml").write_text("")

    assert validation.main(["--workdir", str(tmp_path / "state"), "--cli", str(cli)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pins"] == {
        "eslint": validation.ESLINT_VERSION,
        "@typescript-eslint/parser": validation.TYPESCRIPT_PARSER_VERSION,
        "golangci-lint": validation.GOLANGCI_VERSION,
    }
    assert payload["cases"]["pi-sprite"]["reports"]["scan"]["tool"]["tool"] == "eslint"


def test_harness_rejects_failed_or_incomplete_analyzer_reports() -> None:
    case = validation.CASES[0]
    failed = report(case, "scan")
    failed["status"] = "partial"
    with pytest.raises(RuntimeError, match="expected 'ok'"):
        validation.validate_report(case, "scan", failed)

    missing = report(case, "scan")
    missing["findings"] = []
    with pytest.raises(RuntimeError, match="produced no analyzer findings"):
        validation.validate_report(case, "scan", missing)


@pytest.mark.parametrize(
    "deltas",
    [[], *[[{"status": status}] for status in ("new", "worsened", "improved", "resolved")]],
)
def test_harness_rejects_exact_head_diff_without_unchanged_deltas(
    deltas: list[dict[str, str]],
) -> None:
    case = validation.CASES[0]
    invalid = report(case, "diff")
    invalid["deltas"] = deltas

    with pytest.raises(RuntimeError, match="exact-HEAD diff must produce unchanged deltas"):
        validation.validate_report(case, "diff", invalid)


def test_harness_accepts_only_exact_pinned_golangci_version(monkeypatch) -> None:
    monkeypatch.setattr(
        validation,
        "command",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, "golangci-lint has version 2.1.0 built from abc\n", ""
        ),
    )

    assert validation.pinned_golangci_version() == "2.1.0"


@pytest.mark.parametrize(
    ("stdout", "match"),
    [
        ("golangci-lint has version 2.2.0 built from abc\n", "2.1.0 is required"),
        ("golangci-lint release build\n", "cannot parse"),
    ],
)
def test_harness_rejects_unpinned_or_unparseable_golangci_version(
    stdout: str, match: str, monkeypatch
) -> None:
    monkeypatch.setattr(
        validation,
        "command",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, stdout, ""),
    )

    with pytest.raises(RuntimeError, match=match):
        validation.pinned_golangci_version()


def test_harness_rejects_wrong_golangci_version_before_case_validation(
    tmp_path: Path, monkeypatch
) -> None:
    cli = tmp_path / "cli"
    cli.mkdir()
    (cli / "pyproject.toml").write_text("")
    monkeypatch.setattr(
        validation,
        "command",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, "golangci-lint has version 2.2.0 built from abc\n", ""
        ),
    )
    called = False

    def fake_case(*_args: object) -> dict[str, object]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(validation, "validate_case", fake_case)

    assert validation.main(["--workdir", str(tmp_path / "state"), "--cli", str(cli)]) == 1
    assert called is False


def test_harness_accepts_exact_candidate_local_typescript_versions(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "node_modules" / "@typescript-eslint" / "parser" / "package.json"
    package.parent.mkdir(parents=True)
    package.write_text(json.dumps({"version": validation.TYPESCRIPT_PARSER_VERSION}))

    def fake_command(*args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "node":
            return subprocess.CompletedProcess([], 0, str(package), "")
        return subprocess.CompletedProcess([], 0, f"v{validation.ESLINT_VERSION}\n", "")

    monkeypatch.setattr(validation, "command", fake_command)

    assert validation.pinned_typescript_versions(tmp_path) == {
        "eslint": validation.ESLINT_VERSION,
        "@typescript-eslint/parser": validation.TYPESCRIPT_PARSER_VERSION,
    }


@pytest.mark.parametrize(
    ("eslint_output", "parser_metadata", "match"),
    [
        ("v9.39.0\n", {"version": validation.TYPESCRIPT_PARSER_VERSION}, "9.39.1 is required"),
        ("eslint 9.39.1\n", {"version": validation.TYPESCRIPT_PARSER_VERSION}, "cannot parse"),
        ("v9.39.1\n", {"version": "8.48.0"}, "8.49.0 is required"),
        ("v9.39.1\n", "{malformed", "cannot parse @typescript-eslint/parser package metadata"),
        ("v9.39.1\n", None, "cannot resolve candidate-local"),
    ],
)
def test_harness_rejects_invalid_candidate_local_typescript_version_evidence(
    tmp_path: Path,
    monkeypatch,
    eslint_output: str,
    parser_metadata: dict[str, str] | str | None,
    match: str,
) -> None:
    package = tmp_path / "node_modules" / "@typescript-eslint" / "parser" / "package.json"
    if parser_metadata is not None:
        package.parent.mkdir(parents=True)
        package.write_text(
            parser_metadata if isinstance(parser_metadata, str) else json.dumps(parser_metadata)
        )

    def fake_command(*args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "node":
            return subprocess.CompletedProcess([], 0, str(package), "")
        return subprocess.CompletedProcess([], 0, eslint_output, "")

    monkeypatch.setattr(validation, "command", fake_command)

    with pytest.raises(RuntimeError, match=match):
        validation.pinned_typescript_versions(tmp_path)


def test_harness_rejects_typescript_version_before_case_analysis(
    tmp_path: Path, monkeypatch
) -> None:
    repository = tmp_path / "pi-sprite"
    repository.mkdir()
    analysis_started = False

    def fake_command(*args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "npm":
            return subprocess.CompletedProcess([], 0, "", "")
        if args[0].endswith("eslint"):
            return subprocess.CompletedProcess([], 0, "v9.39.0\n", "")
        raise AssertionError(f"unexpected command: {args}")

    def fake_run_report(*_args: object) -> dict[str, object]:
        nonlocal analysis_started
        analysis_started = True
        return {}

    monkeypatch.setattr(validation, "clone", lambda *_args: repository)
    monkeypatch.setattr(validation, "command", fake_command)
    monkeypatch.setattr(validation, "run_report", fake_run_report)

    with pytest.raises(RuntimeError, match="9.39.1 is required"):
        validation.validate_case(validation.CASES[0], tmp_path, tmp_path)
    assert analysis_started is False


def test_harness_rejects_source_tree_changes_after_provisioning(
    tmp_path: Path, monkeypatch
) -> None:
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, "?? changed-file\n", ""),
        ]
    )
    monkeypatch.setattr(validation, "command", lambda *_args, **_kwargs: next(responses))

    with pytest.raises(RuntimeError, match="changed during validation"):
        validation.clean_tree(tmp_path)
