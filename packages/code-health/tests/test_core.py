from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest
from code_health.core import (
    _analyze_prepared,
    _decorate,
    _deltas,
    _paths_in_scope,
    _prepare_adapters,
    _status,
    _verified_deltas,
    analyze,
)
from code_health.models import Finding, ToolStatus
from code_health.repository import size_metrics


def finding(
    *,
    value: int,
    path: str = "src/app.py",
    symbol: str = "route",
    metric: str = "cyclomatic-complexity",
) -> Finding:
    return Finding(
        tool="ruff",
        rule="C901",
        metric=metric,
        path=path,
        line=10,
        symbol=symbol,
        value=value,
        threshold=10,
        message=f"`{symbol}` is too complex ({value} > 10)",
        scope="non-test",
    )


def test_decorate_prioritizes_changed_high_churn_findings() -> None:
    current = [
        finding(value=11, path="src/stable.py"),
        finding(value=15, path="src/hot.py"),
    ]

    decorated = _decorate(
        current,
        changed={"src/hot.py"},
        churn={"src/hot.py": 400, "src/stable.py": 20},
    )

    assert decorated[0].path == "src/hot.py"
    assert decorated[0].changed is True
    assert decorated[0].churn == 400


def test_deltas_preserve_new_worsened_improved_and_resolved() -> None:
    baseline = [
        finding(value=12, path="src/worse.py"),
        finding(value=18, path="src/better.py"),
        finding(value=14, path="src/gone.py"),
    ]
    current = [
        finding(value=16, path="src/worse.py"),
        finding(value=11, path="src/better.py"),
        finding(value=13, path="src/new.py"),
    ]

    statuses = {delta.path: delta.status for delta in _deltas(current, baseline)}

    assert statuses == {
        "src/better.py": "improved",
        "src/gone.py": "resolved",
        "src/new.py": "new",
        "src/worse.py": "worsened",
    }
    resolved = next(delta for delta in _deltas(current, baseline) if delta.status == "resolved")
    assert resolved.before_finding is not None
    assert resolved.before_finding.path == "src/gone.py"


@pytest.mark.parametrize(
    ("before", "after", "status"),
    [(10, 9, "worsened"), (10, 11, "improved")],
)
def test_deltas_reverse_maintainability_index_direction(
    before: int, after: int, status: str
) -> None:
    baseline = [finding(value=before, metric="maintainability-index")]
    current = [finding(value=after, metric="maintainability-index")]

    assert _deltas(current, baseline)[0].status == status


def test_maintainability_index_deltas_keep_unchanged_new_and_resolved_statuses() -> None:
    baseline = [
        finding(value=10, path="src/unchanged.go", metric="maintainability-index"),
        finding(value=10, path="src/resolved.go", metric="maintainability-index"),
    ]
    current = [
        finding(value=10, path="src/unchanged.go", metric="maintainability-index"),
        finding(value=10, path="src/new.go", metric="maintainability-index"),
    ]

    assert {delta.path: delta.status for delta in _deltas(current, baseline)} == {
        "src/new.go": "new",
        "src/resolved.go": "resolved",
        "src/unchanged.go": "unchanged",
    }


def test_deltas_reject_duplicate_identity_instead_of_overwriting() -> None:
    duplicates = [
        finding(value=11, symbol="First.run"),
        finding(value=12, symbol="First.run"),
    ]

    with pytest.raises(RuntimeError, match="duplicate current finding identity"):
        _deltas(duplicates, [])


def test_deltas_use_line_identity_when_analyzer_has_no_symbol() -> None:
    first = finding(value=11, symbol="")
    second = Finding(
        **{
            **first.__dict__,
            "line": 20,
            "value": 12,
        }
    )

    deltas = _deltas([first, second], [])

    assert len(deltas) == 2
    assert {delta.symbol for delta in deltas} == {"line:10", "line:20"}


def test_size_metrics_separates_python_and_inline_rust_tests(tmp_path: Path) -> None:
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text("one\ntwo\n")
    tests = tmp_path / "tests" / "test_app.py"
    tests.parent.mkdir()
    tests.write_text("a\nb\nc\n")
    rust = tmp_path / "src" / "lib.rs"
    rust.write_text("pub fn run() {}\n#[cfg(test)]\nmod tests {}\n")

    metrics = size_metrics(tmp_path)

    assert metrics["non_test_lines"] == 3
    assert metrics["test_lines"] == 5
    assert metrics["non_test_files"] == 2
    assert metrics["test_files"] == 2


def test_verified_deltas_omit_analyzer_with_snapshot_evidence_gap() -> None:
    baseline = [finding(value=11)]

    deltas, gaps = _verified_deltas(
        [],
        baseline,
        [ToolStatus("ruff", "unavailable", "ambiguous identity")],
        [ToolStatus("ruff", "ok", "baseline evidence")],
    )

    assert deltas == []
    assert gaps == []


def test_unsupported_repository_is_partial_with_explicit_evidence_gap(
    tmp_path: Path,
) -> None:
    findings, tools = _analyze_prepared(tmp_path, tmp_path, [], {})

    assert findings == []
    assert _status(tools) == "partial"
    assert tools[0].tool == "source-analyzer"
    assert tools[0].status == "unavailable"


@pytest.mark.parametrize(
    "language, phase",
    [("typescript", "prepare"), ("typescript", "run"), ("go", "prepare"), ("go", "run")],
)
def test_optional_adapter_runtime_errors_become_partial_tool_status(
    tmp_path: Path, monkeypatch, language: str, phase: str
) -> None:
    def prepare(*_args: object) -> tuple[object, ToolStatus]:
        if phase == "prepare":
            raise RuntimeError("preparation exploded")
        return object(), ToolStatus(language, "ok", "prepared")

    def adapter(*_args: object) -> tuple[list[Finding], ToolStatus]:
        if phase == "run":
            raise RuntimeError("execution exploded")
        return [], ToolStatus(language, "ok", "ran")

    monkeypatch.setattr("code_health.core.ADAPTERS", {language: (prepare, adapter)})
    contexts, preparation = _prepare_adapters(tmp_path, tmp_path, [language], tmp_path)
    findings, execution = _analyze_prepared(tmp_path, tmp_path, [language], contexts)
    statuses = [*preparation, *execution]

    assert findings == []
    assert _status(statuses) == "partial"
    expected = "preparation" if phase == "prepare" else "analysis"
    assert any(status.status == "error" and expected in status.detail for status in statuses)


def test_paths_in_scope_excludes_other_worktree_changes() -> None:
    paths = {
        "config/ai-config/CHANGELOG.md",
        "skills/code-quality/code-health-review/SKILL.md",
        "README.md",
    }

    scoped = _paths_in_scope(
        paths,
        Path("skills/code-quality/code-health-review"),
    )

    assert scoped == {"skills/code-quality/code-health-review/SKILL.md"}


@pytest.mark.parametrize(
    "name", ["app.ts", "view.tsx", "legacy.js", "widget.jsx", "module.mts", "module.cts", "main.go"]
)
def test_size_metrics_supports_typescript_javascript_and_go(tmp_path: Path, name: str) -> None:
    (tmp_path / name).write_text("line\n")
    metrics = size_metrics(tmp_path)
    assert metrics["non_test_files"] == 1


def test_diff_prepares_baseline_only_language_once_and_reports_resolved(
    tmp_path: Path, monkeypatch
) -> None:
    """A removed language still reuses the candidate-resolved adapter context."""
    baseline = tmp_path.parent / "baseline"
    baseline.mkdir()
    (baseline / "removed.go").write_text("package removed\n")
    preparations: list[object] = []
    contexts: list[object] = []

    def prepare(root: Path, temporary: Path, target: Path):
        context = object()
        preparations.append(context)
        return context, ToolStatus("fake-go", "ok", "prepared")

    def adapter(target: Path, root: Path, context: object):
        contexts.append(context)
        if not (target / "removed.go").exists():
            return [], ToolStatus("fake-go", "ok", "candidate")
        return [
            Finding(
                "fake-go",
                "gocyclo",
                "cyclomatic-complexity",
                "removed.go",
                1,
                "line:1:1",
                11,
                10,
                "complexity 11 > 10",
                "non-test",
            )
        ], ToolStatus("fake-go", "ok", "baseline")

    @contextmanager
    def exported(_root: Path, _revision: str):
        yield baseline

    monkeypatch.setattr("code_health.core.ADAPTERS", {"go": (prepare, adapter)})
    monkeypatch.setattr("code_health.core.discover_root", lambda _path: tmp_path)
    monkeypatch.setattr("code_health.core.default_base", lambda _root: "main")
    monkeypatch.setattr("code_health.core.merge_base", lambda _root, _base: "base")
    monkeypatch.setattr("code_health.core.changed_paths", lambda _root, _base: set())
    monkeypatch.setattr("code_health.core.working_tree_paths", lambda _root: set())
    monkeypatch.setattr("code_health.core.churn_by_path", lambda _root, _days: {})
    monkeypatch.setattr("code_health.core.exported_revision", exported)
    monkeypatch.setattr("code_health.core.repository_identity", lambda _root: "test")
    monkeypatch.setattr("code_health.core.revision", lambda _root: "head")
    monkeypatch.setattr("code_health.core.size_metrics", lambda _root: {})

    report = analyze(tmp_path, mode="diff", base=None, churn_days=30)

    assert report.languages == []
    assert report.summary["resolved"] == 1
    assert len(preparations) == 1
    assert contexts == [preparations[0]]


def test_test_path_policy_covers_javascript_and_go_conventions() -> None:
    from code_health.repository import is_test_path

    assert is_test_path(Path("src/app.test.ts"))
    assert is_test_path(Path("__tests__/app.tsx"))
    assert is_test_path(Path("pkg/app_test.go"))
