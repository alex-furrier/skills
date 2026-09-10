import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parents[1]
PLUGIN_SRC = ROOT / "plugins/context-engineering/cli/src"
sys.path.insert(0, str(PLUGIN_SRC))

from context_engineering.analysis import context_check  # noqa: E402
from context_engineering.cli.dispatch import main as cli_main  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True).stdout.strip()


def test_composed_check_retains_review_evidence_for_rename_and_cli_json(tmp_path, capsys):
    repo = tmp_path / "repo"; repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "old.md").write_text("before\n")
    git(repo, "add", "."); git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "mv", "old.md", "new.md")
    git(repo, "commit", "-qm", "rename")
    head = git(repo, "rev-parse", "HEAD")

    result = context_check.analyze(repo, base=base, head=head)
    assert result.data["changed_paths"] == [{"status": "renamed", "path": "new.md", "old_path": "old.md"}]
    assert result.data["evidence"] == [{
        "status": "renamed", "path": "new.md", "old_path": "old.md",
        "source": "git-diff", "range": f"{base}...{head}",
    }]
    assert result.data["advisory_routes"]

    assert cli_main(["check", str(repo), "--base", base, "--head", head, "--json"]) == 0
    emitted = json.loads(capsys.readouterr().out)
    assert emitted["data"]["changed_paths"] == result.data["changed_paths"]
    assert emitted["data"]["evidence"] == result.data["evidence"]
    assert emitted["data"]["advisory_routes"] == result.data["advisory_routes"]


def test_composed_check_preserves_invalid_range_error_protocol(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("text\n")
    git(repo, "add", "."); git(repo, "commit", "-qm", "initial")
    result = context_check.analyze(repo, base="not-a-commit")
    assert result.has_errors
    assert result.data["changed_paths"] == []
    assert result.data["evidence"] == []
    assert result.data["deterministic_errors"][0]["code"] == "invalid-git-range"
