from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "code-health@example.com")
    git(repo, "config", "user.name", "Code Health")
    (repo / "app.py").write_text("def route(value: int) -> int:\n    return value\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "initial")
    return repo


def run_cli(
    repo: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "code_health", *args],
        cwd=repo.parent,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def write_executable(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    path.chmod(0o755)


def test_packaged_cli_version_matches_release_watermark(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    cli_root = Path(__file__).resolve().parents[1]
    version = "0.2.0"

    result = run_cli(repo, "--version")

    assert result.returncode == 0
    assert result.stdout.strip() == f"code-health {version}"
    project = tomllib.loads((cli_root / "pyproject.toml").read_text())
    assert project["project"]["version"] == version
    lock = tomllib.loads((cli_root / "uv.lock").read_text())
    package = next(item for item in lock["package"] if item["name"] == project["project"]["name"])
    assert package["version"] == version


def test_scan_runs_from_unrelated_cwd_and_returns_stable_json(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = run_cli(repo, "scan", str(repo), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["version"] == 1
    assert payload["mode"] == "scan"
    assert payload["repository"] == "sample"
    assert payload["scope"] == "."
    assert payload["churn_days"] == 90
    assert payload["working_tree_paths"] == []
    assert payload["languages"] == ["python"]
    assert payload["size"]["non_test_lines"] == 2
    assert payload["unavailable_metrics"][0]["metric"] == "duplication"


def test_scan_uses_stable_repository_identity_in_worktree(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    worktree = tmp_path / "named-after-task"
    git(repo, "worktree", "add", "-b", "review", str(worktree))

    result = run_cli(worktree, "scan", str(worktree), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["repository"] == "sample"
    assert payload["repository_root"] == str(worktree)


def test_diff_reports_new_complexity_without_gating(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    branches = "\n".join(f"    if value == {index}:\n        value += 1" for index in range(12))
    (repo / "app.py").write_text(
        "def route(value: int) -> int:\n" + branches + "\n    return value\n"
    )

    result = run_cli(
        repo,
        "diff",
        str(repo),
        "--base",
        "main",
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["working_tree_paths"] == ["app.py"]
    assert payload["summary"]["new"] >= 1
    assert any(
        delta["status"] == "new" and delta["metric"] == "cyclomatic-complexity"
        for delta in payload["deltas"]
    )
    delta = next(delta for delta in payload["deltas"] if delta["status"] == "new")
    assert delta["after_finding"]["tool"] == "ruff"
    assert delta["after_finding"]["threshold"] == 10


def test_diff_uses_merge_base_when_main_advances(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    merge_base = git_output(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-c", "feature")
    git(repo, "switch", "main")
    branches = "\n".join(f"    if value == {index}:\n        value += 1" for index in range(12))
    (repo / "app.py").write_text(
        "def route(value: int) -> int:\n" + branches + "\n    return value\n"
    )
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "main advances independently")
    git(repo, "switch", "feature")

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["baseline_revision"] == merge_base
    assert payload["summary"]["resolved"] == 0
    assert payload["deltas"] == []


def test_diff_baseline_includes_export_ignored_source(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    branches = "\n".join(f"    if value == {index}:\n        value += 1" for index in range(12))
    (repo / "ignored.py").write_text(
        "def route(value: int) -> int:\n" + branches + "\n    return value\n"
    )
    (repo / ".gitattributes").write_text("ignored.py export-ignore\n")
    git(repo, "add", "ignored.py", ".gitattributes")
    git(repo, "commit", "-m", "add export-ignored complexity")

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"]["new"] == 0
    assert any(finding["path"] == "ignored.py" for finding in payload["findings"])


def test_diff_runs_real_eslint_subprocess_with_baseline_delta(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").unlink()
    source = repo / "app.ts"
    source.write_text("// baseline\nexport const run = () => 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "add typescript")
    eslint = repo / "node_modules/.bin/eslint"
    write_executable(
        eslint,
        """#!/usr/bin/env python3
import json
import pathlib
import sys
if "--version" in sys.argv:
    print("v9.2.0")
    raise SystemExit(0)
target = pathlib.Path(sys.argv[-1])
source = next(target.rglob("app.ts"))
value = 12 if "candidate" in source.read_text() else 11
message = f"Function 'run' has a complexity of {value}. Maximum allowed is 10"
issue = {"ruleId": "complexity", "line": 2, "column": 1, "message": message}
print(json.dumps([{"filePath": str(source.resolve()), "messages": [issue]}]))
raise SystemExit(1)
""",
    )
    parser = repo / "node_modules/@typescript-eslint/parser/dist/index.js"
    parser.parent.mkdir(parents=True)
    parser.write_text("export default {}\n")
    source.write_text("// candidate\nexport const run = () => 1\n")

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["languages"] == ["typescript"]
    assert payload["summary"]["worsened"] == 1
    assert any(
        item["metric"] == "cyclomatic-complexity"
        and item["before"] == 11
        and item["after"] == 12
        and item["status"] == "worsened"
        for item in payload["deltas"]
    )
    assert not list(repo.rglob("eslint.config.mjs"))
    assert not list(repo.rglob(".eslintcache"))


def test_diff_runs_real_golangci_subprocess_with_baseline_delta(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").unlink()
    (repo / "go.mod").write_text("module example/code-health\n")
    source = repo / "app.go"
    source.write_text("package app\n// baseline\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "add go")
    fake_bin = tmp_path / "bin"
    write_executable(
        fake_bin / "golangci-lint",
        """#!/usr/bin/env python3
import json
import pathlib
import sys
if sys.argv[1:] == ["version"]:
    print("golangci-lint has version 2.1.0")
    raise SystemExit(0)
output = pathlib.Path(sys.argv[sys.argv.index("--output.json.path") + 1])
value = 12 if "candidate" in pathlib.Path("app.go").read_text() else 11
output.parent.mkdir(parents=True, exist_ok=True)
issue = {
    "FromLinter": "gocyclo",
    "Text": f"cyclomatic complexity {value} of func Run is high (> 10)",
    "Pos": {"Filename": "app.go", "Line": 1, "Column": 1},
}
output.write_text(json.dumps({"Issues": [issue]}))
raise SystemExit(1)
""",
    )
    source.write_text("package app\n// candidate\n")
    environment = {**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"}

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "json", env=environment)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["languages"] == ["go"]
    assert payload["summary"]["worsened"] == 1
    assert any(
        item["metric"] == "cyclomatic-complexity"
        and item["before"] == 11
        and item["after"] == 12
        and item["status"] == "worsened"
        for item in payload["deltas"]
    )
    assert not list(repo.rglob("golangci.yml"))
    assert not list(repo.rglob("findings.json"))
    assert not list(repo.rglob("go-cache"))
    assert not list(repo.rglob("lint-cache"))


@pytest.mark.parametrize(
    ("workspace", "module_names", "expected"),
    [
        (None, ("root",), {"root": "off"}),
        (
            'go 1.22\nuse "./listed module"\n',
            ("listed module",),
            {"listed module": "copied"},
        ),
        (
            "go 1.22\nuse (\n  ./listed\n)\n",
            ("listed", "omitted"),
            {"listed": "copied", "omitted": "off"},
        ),
    ],
)
def test_diff_overrides_ambient_gowork_for_candidate_and_baseline(
    tmp_path: Path,
    workspace: str | None,
    module_names: tuple[str, ...],
    expected: dict[str, str],
) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").unlink()
    if workspace is not None:
        (repo / "go.work").write_text(workspace)
    for name in module_names:
        module = repo if name == "root" else repo / name
        module.mkdir(parents=True, exist_ok=True)
        (module / "go.mod").write_text(f"module example/{name}\n")
        (module / "app.go").write_text("package app\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "add go workspace")
    candidate_module = repo if module_names[0] == "root" else repo / module_names[0]
    (candidate_module / "app.go").write_text("package app\n// candidate\n")
    records = tmp_path / "gowork-records.jsonl"
    fake_bin = tmp_path / "bin"
    write_executable(
        fake_bin / "golangci-lint",
        f"""#!/usr/bin/env python3
import json
import os
import pathlib
import sys
if sys.argv[1:] == ["version"]:
    print("golangci-lint has version 2.1.0")
    raise SystemExit(0)
record = {{
    "module": pathlib.Path("go.mod").read_text().removeprefix("module ").strip(),
    "gowork": os.environ.get("GOWORK"),
}}
with pathlib.Path({str(records)!r}).open("a") as destination:
    destination.write(json.dumps(record) + "\\n")
output = pathlib.Path(sys.argv[sys.argv.index("--output.json.path") + 1])
output.write_text('{{"Issues": []}}')
""",
    )
    environment = {
        **os.environ,
        "GOWORK": "/external/go.work",
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "json", env=environment)

    assert result.returncode == 0, result.stderr
    observed = [json.loads(line) for line in records.read_text().splitlines()]
    assert len(observed) == 2 * len(module_names)
    for record in observed:
        mode = expected[record["module"].removeprefix("example/")]
        if mode == "off":
            assert record["gowork"] == "off"
        else:
            assert record["gowork"] != "/external/go.work"
            assert record["gowork"].endswith("/go-analysis/source/go.work")


def test_cli_returns_partial_report_when_optional_eslint_execution_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").unlink()
    (repo / "app.ts").write_text("export const run = () => 1\n")
    eslint = repo / "node_modules/.bin/eslint"
    write_executable(eslint, "#!/missing/interpreter\n")
    parser = repo / "node_modules/@typescript-eslint/parser/dist/index.js"
    parser.parent.mkdir(parents=True)
    parser.write_text("export default {}\n")

    result = run_cli(repo, "scan", str(repo), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "partial"
    assert any(tool["tool"] == "eslint" and tool["status"] == "error" for tool in payload["tools"])


def test_markdown_preserves_provenance_deltas_and_evidence_gaps(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    branches = "\n".join(f"    if value == {index}:\n        value += 1" for index in range(12))
    (repo / "app.py").write_text(
        "def route(value: int) -> int:\n" + branches + "\n    return value\n"
    )

    result = run_cli(repo, "diff", str(repo), "--base", "main", "--format", "markdown")

    assert result.returncode == 0, result.stderr
    assert "ruff:C901" in result.stdout
    assert "## Representative deltas" in result.stdout
    assert "new:" in result.stdout
    assert "duplication: unavailable" in result.stdout


def test_invalid_churn_window_is_usage_error(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    result = run_cli(repo, "scan", str(repo), "--churn-days", "0")

    assert result.returncode == 2
    assert "--churn-days must be greater than 0" in result.stderr
