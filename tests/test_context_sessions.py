"""Portable session ranking uses only explicitly exported artifacts."""
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "packages/context-engineering/src"))

from context_engineering.analysis import sessions  # noqa: E402
from context_engineering.cli.dispatch import main as cli_main  # noqa: E402


def artifact(directory, name, lines, age_days=0):
    path = directory / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    timestamp = time.time() - age_days * 86400
    os.utime(path, (timestamp, timestamp))
    return path


def test_sessions_explicit_directory_and_missing_directory(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    assert sessions.analyze(str(project)).data["state"] == "unavailable"
    assert sessions.analyze(str(project), sessions_dir=str(tmp_path / "missing")).data["state"] == "unavailable"
    exports = tmp_path / "exports"
    exports.mkdir()
    assert sessions.analyze(str(project), sessions_dir=str(exports)).data == {"state": "available", "sessions": []}


def test_sessions_rank_lines_alias_basename_floor_and_limit(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(project, target_is_directory=True)
    exports = tmp_path / "exports"
    exports.mkdir()
    older = artifact(exports, "older.jsonl", [str(project)] * 12, age_days=66)
    recent = artifact(exports, "recent.jsonl", [f"{project} project", "project", "other"], age_days=0)
    tied = artifact(exports, "tied.jsonl", ["project", "project"], age_days=0)
    artifact(exports, "unrelated.jsonl", ["nothing relevant"])

    data = sessions.analyze(str(alias), max_results=2, sessions_dir=str(exports)).data
    assert [item["path"] for item in data["sessions"]] == [str(recent), str(tied)]
    assert data["sessions"][0]["match_count"] == 2  # full path + basename on one line count once
    assert data["sessions"][0]["score"] == 2.0
    assert data["sessions"][0]["recency_weight"] == 1.0
    all_sessions = sessions.analyze(str(alias), sessions_dir=str(exports)).data["sessions"]
    assert all_sessions[2] == {
        "path": str(older), "match_count": 12, "age_days": 66.0,
        "recency_weight": 0.1, "score": 1.2,
    }


def test_sessions_full_path_without_basename_fallback(tmp_path):
    exports = tmp_path / "exports"
    exports.mkdir()
    root = pathlib.Path(tmp_path.anchor)
    match = artifact(exports, "root.jsonl", [str(root)])
    artifact(exports, "unrelated.jsonl", ["no path separator"])

    data = sessions.analyze(str(root), sessions_dir=str(exports)).data
    assert [item["path"] for item in data["sessions"]] == [str(match)]
    assert data["sessions"][0]["match_count"] == 1


def test_sessions_raw_lines_and_unreadable_artifacts(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    exports = tmp_path / "exports"
    exports.mkdir()
    raw = artifact(exports, "raw.jsonl", ["not JSON: project"])
    (exports / "invalid-utf8.jsonl").write_bytes(b"project\xff\n")
    (exports / "broken.jsonl").symlink_to(exports / "absent.jsonl")
    data = sessions.analyze(str(project), sessions_dir=str(exports)).data
    assert [item["path"] for item in data["sessions"]] == [str(raw)]
    assert data["sessions"][0]["match_count"] == 1


def test_sessions_cli_json(tmp_path, capsys):
    project = tmp_path / "project"
    project.mkdir()
    exports = tmp_path / "exports"
    exports.mkdir()
    match = artifact(exports, "match.jsonl", [str(project)])
    assert cli_main(["sessions", str(project), "--sessions-dir", str(exports), "--max", "1", "--json"]) == 0
    emitted = json.loads(capsys.readouterr().out)
    assert emitted["data"]["state"] == "available"
    assert emitted["data"]["sessions"][0]["path"] == str(match)
    assert emitted["data"]["sessions"][0]["match_count"] == 1
