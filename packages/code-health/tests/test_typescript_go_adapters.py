from __future__ import annotations

import json
from pathlib import Path

import pytest
from code_health.analyzers.go import (
    CONFIG,
    GoContext,
    _function_name,
    _metric_value_and_threshold,
    _relative_issue_path,
    _workspace_use_paths,
    prepare_golangci,
    run_golangci,
)
from code_health.analyzers.typescript import (
    ESLINT_RULES,
    NUMBER,
    ESLintContext,
    _typescript_symbol,
    prepare_eslint,
    run_eslint,
)
from code_health.core import DeltaEvidenceGap, _deltas, _verified_deltas
from code_health.models import Finding, ToolStatus
from code_health.process import ProcessResult


def test_golangci_normalizes_relative_and_absolute_paths_and_values(
    tmp_path: Path, monkeypatch
) -> None:
    module = tmp_path / "nested" / "demo"
    source = module / "pkg" / "app.go"
    source.parent.mkdir(parents=True)
    source.write_text("package pkg\n")
    (module / "go.mod").write_text("module example/demo\n")
    temporary = tmp_path / "tool-state"
    temporary.mkdir()
    context = GoContext("golangci-lint", "version 2.1", temporary / "golangci.yml")
    context.config.write_text(CONFIG)

    def fake_run(command, **kwargs):
        copy_root = kwargs["cwd"]
        output = Path(command[command.index("--output.json.path") + 1])
        output.write_text(
            json.dumps(
                {
                    "Issues": [
                        {
                            "FromLinter": "gocyclo",
                            "Text": "cyclomatic complexity 12 of func Run is high (> 10)",
                            "Pos": {"Filename": "pkg/app.go", "Line": 1, "Column": 1},
                        },
                        {
                            "FromLinter": "gocognit",
                            "Text": "cognitive complexity 16 of func Run is high (> 15)",
                            "Pos": {
                                "Filename": str(copy_root / "pkg/app.go"),
                                "Line": 1,
                                "Column": 2,
                            },
                        },
                        {
                            "FromLinter": "funlen",
                            "Text": "Function 'Run' has too many statements (61 > 60)",
                            "Pos": {"Filename": "pkg/app.go", "Line": 1, "Column": 3},
                        },
                        {
                            "FromLinter": "funlen",
                            "Text": "Function 'Run' is too long (101 > 100)",
                            "Pos": {"Filename": "pkg/app.go", "Line": 1, "Column": 4},
                        },
                        {
                            "FromLinter": "maintidx",
                            "Text": (
                                "Function name: Run, Cyclomatic Complexity: 2, Halstead Volume: "
                                "10.00, Maintainability Index: 10"
                            ),
                            "Pos": {"Filename": "pkg/app.go", "Line": 1, "Column": 5},
                        },
                        {
                            "FromLinter": "revive",
                            "Text": (
                                "maximum number of arguments per function exceeded; max 5 but got 6"
                            ),
                            "Pos": {"Filename": "pkg/app.go", "Line": 1, "Column": 6},
                        },
                    ]
                }
            )
        )
        assert not (copy_root / "go-cache").exists()
        assert not (copy_root / "lint-cache").exists()
        assert kwargs["env"] == {
            "GOCACHE": str(temporary / "go-analysis" / "go-cache"),
            "GOMODCACHE": str(temporary / "go-analysis" / "go-mod-cache"),
            "GOLANGCI_LINT_CACHE": str(temporary / "go-analysis" / "lint-cache"),
            "GOPROXY": "off",
            "GOSUMDB": "off",
            "GOTOOLCHAIN": "local",
            "GOWORK": "off",
        }
        return ProcessResult(1, "", "")

    monkeypatch.setattr("code_health.analyzers.go.run", fake_run)
    findings, status = run_golangci(module, tmp_path, context)

    assert status.status == "ok"
    assert "--tests=false" in status.command
    assert "--uniq-by-line=false" in status.command
    assert "--max-issues-per-linter=0" in status.command
    assert "--max-same-issues=0" in status.command
    assert "default: none" in CONFIG
    assert [(item.metric, item.value, item.threshold) for item in findings] == [
        ("cyclomatic-complexity", 12, 10),
        ("cognitive-complexity", 16, 15),
        ("statement-count", 61, 60),
        ("function-lines", 101, 100),
        ("maintainability-index", 10, 20),
        ("argument-count", 6, 5),
    ]
    assert {item.path for item in findings} == {"nested/demo/pkg/app.go"}


def test_golangci_normalizes_disposable_workspace_relative_paths(tmp_path: Path) -> None:
    copy_root = tmp_path / "go-analysis" / "source"

    assert (
        _relative_issue_path("go-analysis/source/pkg/app.go", copy_root, Path(".")) == "pkg/app.go"
    )


def test_golangci_ignores_unrecognized_numeric_message(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "app.go"
    source.write_text("package app\n")
    (tmp_path / "go.mod").write_text("module example/app\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "state.yml")
    context.config.write_text(CONFIG)

    def fake_run(command, **kwargs):
        output = Path(command[command.index("--output.json.path") + 1])
        output.write_text(
            json.dumps(
                {
                    "Issues": [
                        {
                            "FromLinter": "gocyclo",
                            "Text": "unrelated 7 / 2",
                            "Pos": {"Filename": "app.go", "Line": 1},
                        }
                    ]
                }
            )
        )
        return ProcessResult(0, "", "")

    monkeypatch.setattr("code_health.analyzers.go.run", fake_run)
    findings, status = run_golangci(tmp_path, tmp_path, context)
    assert (findings[0].value, findings[0].threshold) == (None, None)
    assert "null value/threshold" in status.detail


def test_golangci_rejects_v1_and_reports_execution_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("code_health.analyzers.go.shutil.which", lambda _: "/bin/golangci-lint")
    monkeypatch.setattr(
        "code_health.analyzers.go.run", lambda *args, **kwargs: ProcessResult(0, "version 1.64", "")
    )
    context, status = prepare_golangci(tmp_path, tmp_path)
    assert context is None and status.status == "unavailable"


def test_eslint_uses_nested_candidate_dependencies_and_named_collision(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "packages" / "web"
    source = package / "src" / "app.ts"
    source.parent.mkdir(parents=True)
    source.write_text("function run(first: number) {}\nfunction run(second: string) {}\n")
    executable = package / "node_modules/.bin/eslint"
    parser = package / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")

    def fake_run(command, **kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.2.0\n", "")
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
                                "message": (
                                    "Function 'run' has a complexity of 11. Maximum allowed is 10"
                                ),
                            },
                            {
                                "ruleId": "complexity",
                                "line": 2,
                                "column": 14,
                                "message": (
                                    "Function 'run' has a complexity of 12. Maximum allowed is 10"
                                ),
                            },
                        ],
                    }
                ]
            ),
            "",
        )

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, status = prepare_eslint(tmp_path, tmp_path / "state", package)
    assert status.status == "ok" and context is not None
    assert context.executable == str(executable)
    findings, result = run_eslint(package, tmp_path, context)
    assert result.status == "ok"
    assert [item.symbol for item in findings] == [
        "run@signature:functionrun(first:number)",
        "run@signature:functionrun(second:string)",
    ]


def test_typescript_symbol_uses_owner_qualified_object_property_arrow(tmp_path: Path) -> None:
    source = tmp_path / "commands.ts"
    source.write_text(
        "export function register() {\n"
        "  return { handler: async (value: string) => value.length };\n"
        "}\n"
    )

    symbol, signature = _typescript_symbol(source, 2, "handler")

    assert symbol == "register.handler"
    assert signature == "handler:async(value:string)"


def test_eslint_unnamed_arrow_diagnostic_uses_assigned_declaration_identity_and_ignores_line_shift(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "package"
    source = package / "app.ts"
    source.parent.mkdir(parents=True)
    executable = package / "node_modules/.bin/eslint"
    parser = package / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")

    def fake_run(command, **_kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.2.0\n", "")
        assert "--no-inline-config" in command
        text = source.read_text()
        line = text.count("\n", 0, text.index("const run")) + 1
        line_start = text.rfind("\n", 0, text.index("=>")) + 1
        column = text.index("=>") - line_start + 1
        return ProcessResult(
            1,
            json.dumps(
                [
                    {
                        "filePath": str(source),
                        "messages": [
                            {
                                "ruleId": "complexity",
                                "line": line,
                                "column": column,
                                "message": (
                                    "Arrow function has a complexity of 11. Maximum allowed is 10"
                                ),
                            }
                        ],
                    }
                ]
            ),
            "",
        )

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, _ = prepare_eslint(tmp_path, tmp_path / "state", package)
    assert context is not None
    source.write_text("/* eslint-disable complexity */\nconst run = () => 1\n")
    baseline, baseline_status = run_eslint(package, tmp_path, context)
    source.write_text("/* eslint-disable complexity */\n\nconst run = () => 1\n")
    candidate, candidate_status = run_eslint(package, tmp_path, context)

    assert baseline_status.status == candidate_status.status == "ok"
    assert baseline[0].symbol == candidate[0].symbol == "run@signature:construn=()"
    assert [delta.status for delta in _deltas(candidate, baseline)] == ["unchanged"]


def test_eslint_unnamed_object_property_arrow_uses_structural_identity_after_line_shift(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "package"
    source = package / "app.ts"
    source.parent.mkdir(parents=True)
    executable = package / "node_modules/.bin/eslint"
    parser = package / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")

    def fake_run(command, **_kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.2.0\n", "")
        text = source.read_text()
        declaration = text.index("handler:")
        line = text.count("\n", 0, declaration) + 1
        line_start = text.rfind("\n", 0, text.index("=>", declaration)) + 1
        column = text.index("=>", declaration) - line_start + 1
        return ProcessResult(
            1,
            json.dumps(
                [
                    {
                        "filePath": str(source),
                        "messages": [
                            {
                                "ruleId": "complexity",
                                "line": line,
                                "column": column,
                                "message": (
                                    "Arrow function has a complexity of 11. Maximum allowed is 10"
                                ),
                            }
                        ],
                    }
                ]
            ),
            "",
        )

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, _ = prepare_eslint(tmp_path, tmp_path / "state", package)
    assert context is not None
    declaration = (
        "export function register() {\n  return { handler: async (value: string) => value };\n}\n"
    )
    source.write_text(declaration)
    baseline, baseline_status = run_eslint(package, tmp_path, context)
    source.write_text("// shifted\n" + declaration)
    candidate, candidate_status = run_eslint(package, tmp_path, context)

    assert baseline_status.status == candidate_status.status == "ok"
    assert (
        baseline[0].symbol
        == candidate[0].symbol
        == ("register.handler@signature:handler:async(value:string)")
    )
    assert [delta.status for delta in _deltas(candidate, baseline)] == ["unchanged"]


def test_typescript_symbol_uses_position_to_reject_inline_callback_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "app.ts"
    text = "const outer = () => items.map(() => 1)\n"
    source.write_text(text)
    inner_column = text.rindex("=>") + 1

    symbol, detail = _typescript_symbol(source, 1, None, inner_column)

    assert symbol is None
    assert detail == "cannot uniquely resolve unnamed arrow declaration on line 1"


def test_typescript_symbol_supports_single_parameter_assigned_arrow_line_shift(
    tmp_path: Path,
) -> None:
    source = tmp_path / "app.ts"
    declaration = "const run = value => value\n"
    source.write_text(declaration)
    column = declaration.index("=>") + 1
    baseline = _typescript_symbol(source, 1, None, column)
    source.write_text("// shifted\n" + declaration)
    candidate = _typescript_symbol(source, 2, None, column)

    assert baseline == candidate == ("run", "construn=value")


def test_golangci_copies_complete_workspace_and_selects_focused_module(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "repo"
    first = root / "first"
    second = root / "second"
    for module in (first, second):
        module.mkdir(parents=True)
        (module / "go.mod").write_text(f"module example/{module.name}\n")
        (module / "app.go").write_text("package app\n")
    (root / "go.work").write_text(
        "go 1.22\n/* workspace modules */\nuse (\n"
        '  "./\\x66irst"\n  /* another module */\n  ./second\n)\n'
    )
    vendor = root / "vendor" / "example.com" / "dependency"
    vendor.mkdir(parents=True)
    (vendor / "dependency.go").write_text("package dependency\n")
    temporary = tmp_path / "state"
    temporary.mkdir()
    context = GoContext("golangci-lint", "version 2", temporary / "golangci.yml")
    context.config.write_text(CONFIG)
    calls: list[Path] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs["cwd"])
        assert (kwargs["cwd"].parents[0] / "go.work").exists()
        assert (kwargs["cwd"].parents[0] / "second" / "go.mod").exists()
        assert (kwargs["cwd"].parents[0] / "vendor/example.com/dependency/dependency.go").exists()
        Path(command[command.index("--output.json.path") + 1]).write_text('{"Issues": []}')
        return ProcessResult(0, "", "")

    monkeypatch.setattr("code_health.analyzers.go.run", fake_run)
    findings, status = run_golangci(first, root, context)
    assert findings == [] and status.status == "ok"
    assert calls == [temporary / "go-analysis" / "source" / "first"]


def test_go_module_resolution_enumerates_scoped_module_container(tmp_path: Path) -> None:
    from code_health.analyzers.go import _modules

    root = tmp_path / "repo"
    scope = root / "services"
    first = scope / "first"
    second = scope / "second"
    outside = root / "outside"
    for module in (first, second, outside):
        module.mkdir(parents=True)
        (module / "go.mod").write_text(f"module example/{module.name}\n")

    assert _modules(scope, root) == [first.resolve(), second.resolve()]


def test_workspace_use_paths_accepts_block_comments_and_go_quoted_escapes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "go.work").write_text(
        "go 1.22\nuse (\n  /* comment spanning\n"
        '     lines */ "./fi\\x72st"\n  "./\\163econd" // another module\n)\n'
    )

    paths, gap = _workspace_use_paths(root)

    assert gap is None
    assert paths == [(root / "first").resolve(), (root / "second").resolve()]


@pytest.mark.parametrize("separator", ["\t", " /* modules */ "])
def test_workspace_use_paths_accepts_go_whitespace_before_block(
    tmp_path: Path, separator: str
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "go.work").write_text(f"go 1.22\nuse{separator}(\n  ./first\n)\n")

    paths, gap = _workspace_use_paths(root)

    assert gap is None
    assert paths == [(root / "first").resolve()]


def test_workspace_use_paths_rejects_unterminated_block_comment(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "go.work").write_text("go 1.22\nuse ./first\n/* unfinished\n")

    paths, gap = _workspace_use_paths(root)

    assert paths is None
    assert gap == "unterminated block comment"


def test_golangci_reports_external_workspace_reference_as_evidence_gap(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "go.mod").write_text("module example/root\n")
    (root / "go.work").write_text("go 1.22\nuse ../outside\n")
    temporary = tmp_path / "state"
    temporary.mkdir()
    context = GoContext("golangci-lint", "version 2", temporary / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(root, root, context)

    assert findings == []
    assert status.status == "unavailable"
    assert "external path" in status.detail


def test_golangci_rejects_absolute_workspace_path_inside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    module = root / "module"
    module.mkdir(parents=True)
    (module / "go.mod").write_text("module example/module\n")
    (root / "go.work").write_text(f"go 1.22\nuse {module}\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(root, root, context)

    assert findings == []
    assert status.status == "unavailable"
    assert "absolute path" in status.detail


def test_golangci_reports_unreadable_workspace_entry_as_evidence_gap(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example/root\n")
    (tmp_path / "go.work").mkdir()
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "unavailable"
    assert "cannot read go.work" in status.detail


def test_golangci_reports_non_utf8_workspace_as_evidence_gap(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example/root\n")
    (tmp_path / "go.work").write_bytes(b"go 1.22\nuse ./module\n\xff")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "unavailable"
    assert "not valid UTF-8" in status.detail


def test_golangci_reports_malformed_workspace_as_evidence_gap(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example/root\n")
    (tmp_path / "go.work").write_text("go 1.22\nuse (\n  ./module\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "unavailable"
    assert "unterminated use block" in status.detail


def test_golangci_reports_execution_failure_without_network_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "go.mod").write_text("module example/root\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)
    monkeypatch.setattr(
        "code_health.analyzers.go.run",
        lambda *_args, **_kwargs: ProcessResult(2, "", "offline miss"),
    )

    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "error"
    assert "offline miss" in status.detail


def test_go_fixed_diagnostic_forms_do_not_guess_values() -> None:
    assert _metric_value_and_threshold(
        "revive", "maximum number of arguments per function exceeded; got 6 but max 5"
    ) == ("argument-count", 6, 5)
    assert _metric_value_and_threshold("maintidx", "MaintIdx: 10") == (
        "maintainability-index",
        None,
        None,
    )
    assert _metric_value_and_threshold("funlen", "unrelated (61 > 60)") == (
        "function-lines",
        None,
        None,
    )


@pytest.mark.parametrize(
    ("rule", "message", "value", "threshold"),
    [
        ("max-params", "(6). Maximum allowed is 5", 6, 5),
        ("max-depth", "(5). Maximum allowed is 4", 5, 4),
        ("max-lines-per-function", "(101). Maximum allowed is 100", 101, 100),
        ("max-nested-callbacks", "(4). Maximum allowed is 3", 4, 3),
        ("complexity", "of 11. Maximum allowed is 10", 11, 10),
    ],
)
def test_eslint_fixed_diagnostic_forms_parse_and_higher_values_worsen(
    rule: str, message: str, value: int, threshold: int
) -> None:
    match = NUMBER.search(message)
    assert match is not None
    assert (int(match.group(1)), int(match.group(2))) == (value, threshold)
    metric, configured_threshold = ESLINT_RULES[rule]
    assert configured_threshold == threshold
    baseline = Finding(
        "eslint",
        rule,
        metric,
        "src/app.ts",
        1,
        "run@line:1:column:1",
        value,
        threshold,
        message,
        "non-test",
    )
    current = Finding(
        "eslint",
        rule,
        metric,
        "src/app.ts",
        1,
        "run@line:1:column:1",
        value + 1,
        threshold,
        message,
        "non-test",
    )

    assert _deltas([current], [baseline])[0].status == "worsened"


def test_eslint_fatal_diagnostic_is_an_evidence_gap_and_suppresses_deltas(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "app.ts"
    source.write_text("function run() {}\n")
    # The adapter only needs an executable/config context for a mocked invocation.
    context = ESLintContext("eslint", "parser", "v9.0.0", tmp_path / "eslint.config.mjs", tmp_path)
    context.config.write_text("")

    monkeypatch.setattr(
        "code_health.analyzers.typescript.run",
        lambda *_args, **_kwargs: ProcessResult(
            1,
            json.dumps(
                [
                    {
                        "filePath": str(source),
                        "fatalErrorCount": 1,
                        "messages": [
                            {"fatal": True, "message": "Parsing error: unexpected token"},
                            {"ruleId": "complexity", "message": "ignored"},
                        ],
                    }
                ]
            ),
            "",
        ),
    )
    findings, status = run_eslint(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "error"
    assert "fatal/parser diagnostic" in status.detail
    prior = Finding(
        "eslint", "complexity", "cyclomatic-complexity", "app.ts", 1, "run", 11, 10, "", "non-test"
    )
    usable = ToolStatus("eslint", "ok", "")
    assert _verified_deltas(findings, [prior], [status], [usable]) == ([], [])
    assert _verified_deltas([prior], findings, [usable], [status]) == ([], [])


def test_eslint_same_line_named_findings_have_unique_delta_identities(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "package"
    source = package / "app.ts"
    source.parent.mkdir(parents=True)
    source.write_text("export const run = () => 1\n")
    executable = package / "node_modules/.bin/eslint"
    parser = package / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")

    def fake_run(command, **kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.2.0\n", "")
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
                                "column": 5,
                                "message": (
                                    "Function 'run' has a complexity of 11. Maximum allowed is 10"
                                ),
                            },
                            {
                                "ruleId": "complexity",
                                "line": 1,
                                "column": 15,
                                "message": (
                                    "Function 'run' has a complexity of 12. Maximum allowed is 10"
                                ),
                            },
                        ],
                    }
                ]
            ),
            "",
        )

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, _ = prepare_eslint(tmp_path, tmp_path / "state", package)
    assert context is not None
    findings, result = run_eslint(package, tmp_path, context)
    assert findings == []
    assert result.status == "unavailable"
    assert "cannot distinguish duplicate" in result.detail


def test_eslint_delta_identity_stays_stable_when_duplicate_is_added(
    tmp_path: Path, monkeypatch
) -> None:
    package = tmp_path / "package"
    source = package / "app.ts"
    source.parent.mkdir(parents=True)
    source.write_text("const worker = {\n  run(existing: number) {}\n};\n")
    executable = package / "node_modules/.bin/eslint"
    parser = package / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")
    messages = [
        {
            "ruleId": "complexity",
            "line": 2,
            "column": 3,
            "message": "Method 'run' has a complexity of 11. Maximum allowed is 10",
        },
    ]

    def fake_run(command, **kwargs):
        if "--version" in command:
            return ProcessResult(0, "v9.2.0\\n", "")
        return ProcessResult(1, json.dumps([{"filePath": str(source), "messages": messages}]), "")

    monkeypatch.setattr("code_health.analyzers.typescript.run", fake_run)
    context, _ = prepare_eslint(tmp_path, tmp_path / "state", package)
    assert context is not None
    baseline, _ = run_eslint(package, tmp_path, context)
    source.write_text(
        "const worker = {\n  run(inserted: string) {}\n  run(existing: number) {}\n};\n"
    )
    messages[:] = [
        {
            "ruleId": "complexity",
            "line": 2,
            "column": 3,
            "message": "Method 'run' has a complexity of 12. Maximum allowed is 10",
        },
        {
            "ruleId": "complexity",
            "line": 3,
            "column": 3,
            "message": "Method 'run' has a complexity of 11. Maximum allowed is 10",
        },
    ]
    current, _ = run_eslint(package, tmp_path, context)
    assert [delta.status for delta in _deltas(current, baseline)] == ["unchanged", "new"]


def test_eslint_signature_edit_reconciles_by_structural_owner_and_name() -> None:
    baseline = Finding(
        "eslint",
        "max-params",
        "argument-count",
        "app.ts",
        1,
        "run@signature:functionrun(a:number,b:number,c:number,d:number,e:number,f:number)",
        6,
        5,
        "",
        "non-test",
    )
    candidate = Finding(
        "eslint",
        "max-params",
        "argument-count",
        "app.ts",
        1,
        "run@signature:functionrun(a:number,b:number,c:number,d:number,e:number,f:number,g:number)",
        7,
        5,
        "",
        "non-test",
    )

    deltas = _deltas([candidate], [baseline])
    assert [(delta.status, delta.before, delta.after) for delta in deltas] == [("worsened", 6, 7)]


def test_eslint_ambiguous_duplicate_signature_edits_are_an_evidence_gap() -> None:
    def finding(signature: str, value: int) -> Finding:
        return Finding(
            "eslint",
            "max-params",
            "argument-count",
            "app.ts",
            1,
            f"worker.run@signature:{signature}",
            value,
            5,
            "",
            "non-test",
        )

    baseline = [finding("run(a:number)", 6), finding("run(b:string)", 6)]
    candidate = [finding("run(c:boolean)", 7), finding("run(d:object)", 7)]

    with pytest.raises(DeltaEvidenceGap, match="cannot reconcile changed TypeScript"):
        _deltas(candidate, baseline)

    deltas, gaps = _verified_deltas(
        candidate,
        baseline,
        [ToolStatus("eslint", "ok", "candidate evidence")],
        [ToolStatus("eslint", "ok", "baseline evidence")],
    )
    assert deltas == []
    assert [(gap.tool, gap.status) for gap in gaps] == [("eslint-delta", "unavailable")]


def test_typescript_identity_qualifies_class_and_object_owners(tmp_path: Path) -> None:
    source = tmp_path / "app.ts"
    source.write_text(
        "class Server {\n  run(value: number) {}\n}\n"
        "const worker = {\n  run(value: string) {}\n};\n"
    )

    assert _typescript_symbol(source, 2, "run") == ("Server.run", "run(value:number)")
    assert _typescript_symbol(source, 5, "run") == ("worker.run", "run(value:string)")


def test_named_function_deltas_ignore_line_shifts_and_disambiguate_duplicates() -> None:
    baseline = [
        Finding(
            "eslint",
            "complexity",
            "cyclomatic-complexity",
            "app.ts",
            1,
            "run",
            11,
            10,
            "",
            "non-test",
        ),
        Finding(
            "golangci-lint",
            "gocyclo",
            "cyclomatic-complexity",
            "app.go",
            1,
            "Run",
            11,
            10,
            "",
            "non-test",
        ),
    ]
    candidate = [
        Finding(
            "eslint",
            "complexity",
            "cyclomatic-complexity",
            "app.ts",
            10,
            "run",
            11,
            10,
            "",
            "non-test",
        ),
        Finding(
            "golangci-lint",
            "gocyclo",
            "cyclomatic-complexity",
            "app.go",
            10,
            "Run",
            11,
            10,
            "",
            "non-test",
        ),
    ]

    assert [delta.status for delta in _deltas(candidate, baseline)] == ["unchanged", "unchanged"]


def test_go_function_identity_qualifies_same_named_methods_by_receiver(tmp_path: Path) -> None:
    source = tmp_path / "app.go"
    source.write_text(
        "package app\n"
        "func (server *Server) Run() {}\n"
        "func (worker Worker[T]) Run() {}\n"
        "func (pair Pair[A, B]) Run() {}\n"
        "func (trio Trio[X, B]) Run() {}\n"
    )

    assert _function_name(source, 2, "Function 'Run'") == ("Server.Run", None)
    assert _function_name(source, 3, "Function 'Run'") == ("Worker.Run", None)
    assert _function_name(source, 4, "Function 'Run'") == ("Pair.Run", None)
    assert _function_name(source, 5, "Function 'Run'") == ("Trio.Run", None)


def test_go_generic_receiver_binder_renames_do_not_change_delta_identity(tmp_path: Path) -> None:
    source = tmp_path / "app.go"
    source.write_text("package app\nfunc (pair Pair[A, B]) Run() {}\n")
    baseline = Finding(
        "golangci-lint",
        "gocyclo",
        "cyclomatic-complexity",
        "app.go",
        2,
        _function_name(source, 2, "Function 'Run'")[0] or "",
        11,
        10,
        "",
        "non-test",
    )
    source.write_text(
        "package app\nfunc (pair Pair[First, Second]) Run() {}\nfunc (other Other[A, B]) Run() {}\n"
    )
    candidate = [
        Finding(
            "golangci-lint",
            "gocyclo",
            "cyclomatic-complexity",
            "app.go",
            line,
            _function_name(source, line, "Function 'Run'")[0] or "",
            11,
            10,
            "",
            "non-test",
        )
        for line in (2, 3)
    ]

    assert baseline.symbol == candidate[0].symbol == "Pair.Run"
    assert candidate[1].symbol == "Other.Run"
    assert sorted(delta.status for delta in _deltas(candidate, [baseline])) == ["new", "unchanged"]


def test_golangci_named_function_delta_ignores_line_shift(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "go.mod").write_text("module example/app\n")
    source = tmp_path / "app.go"
    state = tmp_path.parent / f"{tmp_path.name}-state"
    state.mkdir()
    context = GoContext("golangci-lint", "version 2", state / "golangci.yml")
    context.config.write_text(CONFIG)

    def fake_run(command, **_kwargs):
        line = source.read_text().count("\n", 0, source.read_text().index("func Run")) + 1
        Path(command[command.index("--output.json.path") + 1]).write_text(
            json.dumps(
                {
                    "Issues": [
                        {
                            "FromLinter": "gocyclo",
                            "Text": "cyclomatic complexity 11 of func Run is high (> 10)",
                            "Pos": {"Filename": "app.go", "Line": line, "Column": 1},
                        }
                    ]
                }
            )
        )
        return ProcessResult(1, "", "")

    monkeypatch.setattr("code_health.analyzers.go.run", fake_run)
    source.write_text("package app\nfunc Run() {}\n")
    baseline, _ = run_golangci(tmp_path, tmp_path, context)
    source.write_text("package app\n\nfunc Run() {}\n")
    candidate, _ = run_golangci(tmp_path, tmp_path, context)

    assert baseline[0].symbol == candidate[0].symbol == "Run"
    assert [delta.status for delta in _deltas(candidate, baseline)] == ["unchanged"]


def test_golangci_typecheck_is_an_evidence_gap(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "app.go").write_text("package app\n")
    (tmp_path / "go.mod").write_text("module example/app\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    def fake_run(command, **_kwargs):
        Path(command[command.index("--output.json.path") + 1]).write_text(
            json.dumps({"Issues": [{"FromLinter": "typecheck", "Text": "undefined: missing"}]})
        )
        return ProcessResult(1, "", "")

    monkeypatch.setattr("code_health.analyzers.go.run", fake_run)
    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "error"
    assert "typecheck diagnostic" in status.detail


@pytest.mark.parametrize("target", ["../outside", "missing"])
def test_golangci_rejects_external_and_dangling_symlinks(tmp_path: Path, target: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "go.mod").write_text("module example/app\n")
    if target == "../outside":
        (tmp_path / "outside").write_text("secret")
    (root / "linked.go").symlink_to(target)
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)

    findings, status = run_golangci(root, root, context)

    assert findings == []
    assert status.status == "error"
    assert "cannot safely copy symlink" in status.detail


def test_golangci_reports_disposable_copy_failure(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "go.mod").write_text("module example/app\n")
    context = GoContext("golangci-lint", "version 2", tmp_path / "golangci.yml")
    context.config.write_text(CONFIG)
    monkeypatch.setattr(
        "code_health.analyzers.go.shutil.copytree",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("copy failed")),
    )

    findings, status = run_golangci(tmp_path, tmp_path, context)

    assert findings == []
    assert status.status == "error"
    assert "cannot create disposable Go workspace copy" in status.detail


def test_eslint_rejects_incompatible_version_and_reports_execution_error(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "node_modules/.bin/eslint"
    parser = tmp_path / "node_modules/@typescript-eslint/parser/dist/index.js"
    executable.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True)
    executable.write_text("")
    parser.write_text("")
    monkeypatch.setattr(
        "code_health.analyzers.typescript.run",
        lambda *args, **kwargs: ProcessResult(0, "v8.0.0", ""),
    )
    context, status = prepare_eslint(tmp_path, tmp_path / "state")
    assert context is None and status.status == "unavailable"
