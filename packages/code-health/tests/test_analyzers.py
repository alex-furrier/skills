from __future__ import annotations

import json
from pathlib import Path

from code_health.analyzers import python as analyzers
from code_health.analyzers import rust
from code_health.process import ProcessResult


def test_ruff_preserves_raw_metric_and_ignores_tests(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text("def route():\n    return 1\n")
    test_source = tmp_path / "tests" / "test_app.py"
    test_source.parent.mkdir()
    test_source.write_text("def test_route():\n    assert True\n")
    payload = [
        {
            "code": "C901",
            "filename": str(source),
            "location": {"row": 1, "column": 1},
            "message": "`route` is too complex (15 > 10)",
        },
        {
            "code": "C901",
            "filename": str(test_source),
            "location": {"row": 1, "column": 1},
            "message": "`test_route` is too complex (20 > 10)",
        },
    ]
    monkeypatch.setattr(analyzers.shutil, "which", lambda _: "/usr/bin/ruff")
    monkeypatch.setattr(
        analyzers,
        "run",
        lambda *args, **kwargs: ProcessResult(0, json.dumps(payload), ""),
    )

    findings, status = analyzers.run_ruff(tmp_path, tmp_path)

    assert status.status == "ok"
    assert len(findings) == 1
    assert findings[0].path == "src/app.py"
    assert findings[0].symbol == "route"
    assert findings[0].value == 15
    assert findings[0].threshold == 10
    assert findings[0].tool == "ruff"
    assert findings[0].rule == "C901"


def test_ruff_resolves_symbol_when_message_omits_it(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text(
        "def first():\n"
        "    if True:\n"
        "        return 1\n"
        "\n"
        "def second():\n"
        "    if True:\n"
        "        return 2\n"
    )
    payload = [
        {
            "code": "PLR0912",
            "filename": str(source),
            "location": {"row": 2, "column": 1},
            "message": "Too many branches (14 > 12)",
        },
        {
            "code": "PLR0912",
            "filename": str(source),
            "location": {"row": 6, "column": 1},
            "message": "Too many branches (18 > 12)",
        },
    ]
    monkeypatch.setattr(analyzers.shutil, "which", lambda _: "/usr/bin/ruff")
    monkeypatch.setattr(
        analyzers,
        "run",
        lambda *args, **kwargs: ProcessResult(0, json.dumps(payload), ""),
    )

    findings, _ = analyzers.run_ruff(tmp_path, tmp_path)

    assert [finding.symbol for finding in findings] == ["first", "second"]
    assert len({finding.key for finding in findings}) == 2


def test_ruff_prefers_qualified_symbols_for_same_named_methods(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "app.py"
    source.write_text(
        "class First:\n"
        "    def run(self):\n"
        "        return 1\n"
        "\n"
        "class Second:\n"
        "    def run(self):\n"
        "        return 2\n"
    )
    payload = [
        {
            "code": "C901",
            "filename": str(source),
            "location": {"row": 2, "column": 5},
            "message": "`run` is too complex (15 > 10)",
        },
        {
            "code": "C901",
            "filename": str(source),
            "location": {"row": 6, "column": 5},
            "message": "`run` is too complex (16 > 10)",
        },
    ]
    monkeypatch.setattr(analyzers.shutil, "which", lambda _: "/usr/bin/ruff")
    monkeypatch.setattr(
        analyzers,
        "run",
        lambda *args, **kwargs: ProcessResult(0, json.dumps(payload), ""),
    )

    findings, _ = analyzers.run_ruff(tmp_path, tmp_path)

    assert [finding.symbol for finding in findings] == ["First.run", "Second.run"]
    assert len({finding.key for finding in findings}) == 2


def test_ruff_uses_shared_test_path_policy(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "router_test.py"
    source.write_text("def route():\n    return 1\n")
    payload = [
        {
            "code": "C901",
            "filename": str(source),
            "location": {"row": 1, "column": 1},
            "message": "`route` is too complex (15 > 10)",
        }
    ]
    monkeypatch.setattr(analyzers.shutil, "which", lambda _: "/usr/bin/ruff")
    monkeypatch.setattr(
        analyzers,
        "run",
        lambda *args, **kwargs: ProcessResult(0, json.dumps(payload), ""),
    )

    findings, _ = analyzers.run_ruff(tmp_path, tmp_path)

    assert findings == []


def test_clippy_preserves_provenance_and_reads_symbol(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\nversion='0.1.0'\n")
    source = tmp_path / "src" / "lib.rs"
    source.parent.mkdir()
    source.write_text("pub fn reduce() {}\n")
    payload = {
        "reason": "compiler-message",
        "message": {
            "code": {"code": "clippy::cognitive_complexity"},
            "message": "the function has a cognitive complexity of (49/25)",
            "spans": [
                {
                    "file_name": "src/lib.rs",
                    "line_start": 1,
                    "is_primary": True,
                }
            ],
        },
    }
    monkeypatch.setattr(rust.shutil, "which", lambda _: "/usr/bin/cargo")
    metadata = {
        "packages": [{"targets": [{"kind": ["lib"]}]}],
    }

    def fake_run(command, **kwargs):
        body = metadata if "metadata" in command else payload
        return ProcessResult(0, json.dumps(body), "")

    monkeypatch.setattr(rust, "run", fake_run)

    findings, status = rust.run_clippy(tmp_path, tmp_path)

    assert status.status == "ok"
    assert len(findings) == 1
    assert findings[0].path == "src/lib.rs"
    assert findings[0].symbol == "reduce"
    assert findings[0].metric == "cognitive-complexity"
    assert findings[0].value == 49
    assert findings[0].threshold == 25
    assert "library targets" in status.detail


def test_clippy_supports_nested_binary_crate_and_qualified_impl(
    tmp_path: Path,
    monkeypatch,
) -> None:
    crate = tmp_path / "tools" / "demo"
    crate.mkdir(parents=True)
    (crate / "Cargo.toml").write_text("[package]\nname='demo'\nversion='0.1.0'\n")
    source = crate / "src" / "main.rs"
    source.parent.mkdir()
    source.write_text("struct First;\nimpl First {\n    fn run() {}\n}\n")
    payload = {
        "reason": "compiler-message",
        "message": {
            "code": {"code": "clippy::too_many_lines"},
            "message": "this function has too many lines (120/100)",
            "spans": [
                {
                    "file_name": "src/main.rs",
                    "line_start": 3,
                    "is_primary": True,
                }
            ],
        },
    }
    metadata = {"packages": [{"targets": [{"kind": ["bin"]}]}]}
    commands: list[tuple[str, ...]] = []

    def fake_run(command, **kwargs):
        commands.append(tuple(command))
        body = metadata if "metadata" in command else payload
        return ProcessResult(0, json.dumps(body), "")

    monkeypatch.setattr(rust.shutil, "which", lambda _: "/usr/bin/cargo")
    monkeypatch.setattr(rust, "run", fake_run)

    findings, status = rust.run_clippy(crate, tmp_path)

    assert status.status == "ok"
    assert "binary targets" in status.detail
    assert findings[0].path == "tools/demo/src/main.rs"
    assert findings[0].symbol == "First::run"
    assert any("--bins" in command for command in commands)
    clippy_call = next(command for command in commands if "clippy" in command)
    assert "--locked" in clippy_call


def test_clippy_covers_workspace_and_isolates_build_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "Cargo.toml").write_text("[workspace]\nmembers=['member']\n")
    source = tmp_path / "member" / "src" / "lib.rs"
    source.parent.mkdir(parents=True)
    source.write_text("pub fn run() {}\n")
    vendored = tmp_path / "vendor" / "crate" / "lib.rs"
    vendored.parent.mkdir(parents=True)
    vendored.write_text("pub fn dependency() {}\n")
    metadata = {
        "workspace_members": ["demo 0.1.0 (path+file:///member)", "other"],
        "packages": [{"targets": [{"kind": ["lib"]}]}],
    }
    calls: list[tuple[tuple[str, ...], dict]] = []
    copied_vendor_seen = False

    def fake_run(command, **kwargs):
        nonlocal copied_vendor_seen
        calls.append((tuple(command), kwargs))
        copied_vendor_seen = (
            copied_vendor_seen or (kwargs["cwd"] / "vendor" / "crate" / "lib.rs").exists()
        )
        if "clippy" in command:
            (kwargs["cwd"] / "build-script-side-effect.txt").write_text("isolated\n")
        body = metadata if "metadata" in command else {}
        return ProcessResult(0, json.dumps(body), "")

    monkeypatch.setattr(rust.shutil, "which", lambda _: "/usr/bin/cargo")
    monkeypatch.setattr(rust, "run", fake_run)

    _, status = rust.run_clippy(tmp_path, tmp_path)

    assert status.status == "ok"
    assert "<disposable-copy>/Cargo.toml" in status.command
    assert str(tmp_path) not in " ".join(status.command)
    assert "CARGO_TARGET_DIR=<temporary>" in status.command
    assert "disposable source copy" in status.detail
    metadata_command, metadata_kwargs = next(call for call in calls if "metadata" in call[0])
    clippy_command, clippy_kwargs = next(call for call in calls if "clippy" in call[0])
    assert "--locked" in metadata_command
    assert metadata_kwargs["cwd"] != tmp_path
    assert copied_vendor_seen
    assert "--workspace" in clippy_command
    assert "--locked" in clippy_command
    cargo_target = Path(clippy_kwargs["env"]["CARGO_TARGET_DIR"])
    assert cargo_target.is_absolute()
    assert not cargo_target.is_relative_to(tmp_path)
    assert clippy_kwargs["cwd"] != tmp_path
    assert not (tmp_path / "build-script-side-effect.txt").exists()


def test_rust_symbols_qualify_same_named_impl_methods(tmp_path: Path) -> None:
    source = tmp_path / "lib.rs"
    source.write_text(
        "struct First;\n"
        "impl First {\n"
        "    fn run() {}\n"
        "}\n"
        "struct Second;\n"
        "impl Second {\n"
        "    fn run() {}\n"
        "}\n"
    )

    assert rust._rust_symbol(tmp_path, "lib.rs", 3) == "First::run"
    assert rust._rust_symbol(tmp_path, "lib.rs", 7) == "Second::run"


def test_missing_optional_analyzer_is_explicit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(analyzers.shutil, "which", lambda _: None)

    findings, status = analyzers.run_ruff(tmp_path, tmp_path)

    assert findings == []
    assert status.status == "unavailable"
    assert "not installed" in status.detail


def test_eslint_uses_fixed_syntax_config_and_line_column_identity(
    tmp_path: Path, monkeypatch
) -> None:
    from code_health.analyzers.typescript import prepare_eslint, run_eslint

    source = tmp_path / "src" / "app.ts"
    source.parent.mkdir()
    source.write_text("export const run = () => 1\n")
    parser = tmp_path / "node_modules/@typescript-eslint/parser/dist/index.js"
    parser.parent.mkdir(parents=True)
    parser.write_text("")
    executable = tmp_path / "node_modules/.bin/eslint"
    executable.parent.mkdir(parents=True)
    executable.write_text("")

    def fake_run(command, **kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.1.0\n", "")
        return ProcessResult(
            1,
            json.dumps(
                [
                    {
                        "filePath": str(source),
                        "messages": [
                            {
                                "ruleId": "complexity",
                                "line": 1,
                                "column": 14,
                                "message": "Function has a complexity of 11. Maximum allowed is 10",
                            }
                        ],
                    }
                ]
            ),
            "",
        )

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, status = prepare_eslint(tmp_path, tmp_path / "temp")
    assert status.status == "ok" and context is not None
    findings, result = run_eslint(tmp_path, tmp_path, context)
    assert result.status == "ok" and findings[0].symbol == "line:1:column:14"
    assert (findings[0].value, findings[0].threshold) == (11, 10)
    config = context.config.read_text()
    assert "max-lines-per-function':['warn',100]" in config
    assert "max-params':['warn',5]" in config


def test_eslint_reports_missing_candidate_parser(tmp_path: Path, monkeypatch) -> None:
    from code_health.analyzers.typescript import prepare_eslint

    executable = tmp_path / "node_modules/.bin/eslint"
    executable.parent.mkdir(parents=True)
    executable.write_text("")
    context, status = prepare_eslint(tmp_path, tmp_path)
    assert context is None and status.status == "unavailable"
    assert "parser" in status.detail


def test_golangci_reports_missing_tool_as_evidence_gap(tmp_path: Path, monkeypatch) -> None:
    from code_health.analyzers.go import prepare_golangci

    monkeypatch.setattr("code_health.analyzers.go.shutil.which", lambda _: None)
    context, status = prepare_golangci(tmp_path, tmp_path)
    assert context is None
    assert status.status == "unavailable"
    assert "v2" in status.detail


def test_go_module_resolution_enumerates_root_and_nested_or_focuses_nearest(tmp_path: Path) -> None:
    from code_health.analyzers.go import _modules

    (tmp_path / "go.mod").write_text("module example/root\n")
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "go.mod").write_text("module example/first\n")
    (second / "go.mod").write_text("module example/second\n")
    nested = first / "pkg"
    nested.mkdir()
    (nested / "app.go").write_text("package pkg\n")
    sibling = second / "pkg"
    sibling.mkdir()
    (sibling / "app.go").write_text("package pkg\n")
    assert _modules(tmp_path, tmp_path) == [tmp_path, first, second]
    assert _modules(nested, tmp_path) == [first]
    assert _modules(sibling, tmp_path) == [second]
