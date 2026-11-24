"""Real Git fixtures for the shared source review surface."""

import json
import subprocess
from pathlib import Path

import pytest
from code_health import shared_decisions as sd
from code_health.cli import main


def git(p, *args):
    return subprocess.check_output(["git", "-C", p, *args], text=True).strip()


@pytest.fixture()
def repo(tmp_path):
    git(tmp_path, "init", "--quiet")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    return tmp_path


SOURCES = {
    "py": """def selected(item, fallback):
    if item is None:
        return fallback
    if not item.allowed:
        return fallback
    return item.preferred_name
""",
    "go": """func selected(item *Item, fallback string) string {
    if item == nil {
        return fallback
    }
    if !item.Allowed { return fallback }
    return item.PreferredName
}
""",
    "ts": """function selected(item: Item, fallback: string) {
    if (item === undefined) {
        return fallback;
    }
    if (!item.allowed) return fallback;
    return item.preferredName;
}
""",
    "rs": """fn selected(item: Option<Item>, fallback: String) -> String {
    if item.is_none() {
        return fallback;
    }
    let item = item.unwrap();
    if !item.allowed { return fallback; }
    item.preferred_name
}
""",
}


@pytest.mark.parametrize("suffix", SOURCES)
def test_all_languages_with_unchanged_counterpart_and_negative_control(repo, suffix):
    src = SOURCES[suffix]
    for name, text in [("a", src), ("c", src.replace("fallback", "different"))]:
        (repo / f"{name}.{suffix}").write_text(text)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    base = git(repo, "rev-parse", "HEAD")
    (repo / f"b.{suffix}").write_text(src)
    git(repo, "add", ".")
    rel = {f"b.{suffix}"}
    result = sd.collect(repo, Path("."), rel, base)
    assert result.status == "ok"
    assert [(m.left.path, m.right.path) for m in result.matches] == [
        (f"a.{suffix}", f"b.{suffix}")
    ]


def test_diff_ignores_old_pair_after_an_unrelated_edit(repo, capsys):
    for name in ("a", "b"):
        (repo / f"{name}.py").write_text(SOURCES["py"] + "\n\n# unrelated\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "existing pair")
    with (repo / "b.py").open("a") as f:
        print("other = True", file=f)
    assert main(["diff", str(repo), "--base", "HEAD", "--format", "json"]) == 0
    evidence = json.loads(capsys.readouterr().out)["shared_decisions"]
    assert evidence["reviewed_files"] == 2
    assert evidence["matches"] == []
    assert main(["scan", str(repo)]) == 0
    text = capsys.readouterr().out
    assert "a.py:1-6" in text and "b.py:1-6" in text


def test_generated_untracked_test_and_symlink_cannot_be_evidence(repo):
    src = SOURCES["py"]
    for name in ("only.py", "test_one.py", "loose.py", "generated.py"):
        (repo / name).write_text(
            ("# Code generated: do not edit.\n" if name == "generated.py" else "") + src
        )
    (repo / "link.py").symlink_to(repo / "only.py")
    git(repo, "add", "only.py", "test_one.py", "link.py", "generated.py")
    data = sd.collect(repo, Path("."), None)
    assert data.matches == [] and data.reviewed_files == 1
    assert data.skipped == {"generated header": 1, "symbolic or outside path": 1}


def test_bounds_and_boilerplate_are_visible(repo, monkeypatch):
    for n in range(sd.MAX_COPIES + 1):
        (repo / f"a{n}.py").write_text(SOURCES["py"])
    git(repo, "add", ".")
    data = sd.collect(repo, Path("."), None)
    assert not data.matches and data.skipped["frequent window suppressed"] == 1
    monkeypatch.setattr(sd, "MAX_FILES", 1)
    data = sd.collect(repo, Path("."), None)
    assert data.status == "partial" and data.skipped["repository budget reached"] == 1


@pytest.mark.parametrize("suffix", SOURCES)
def test_single_side_changed_on_guard_points_at_unchanged_peer(repo, suffix, capsys):
    src = SOURCES[suffix]
    for name in ("left", "right"):
        (repo / f"{name}.{suffix}").write_text(src)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "old")
    old = git(repo, "rev-parse", "HEAD")
    (repo / f"left.{suffix}").write_text(
        src.replace("return fallback", "return defaultValue", 1)
    )
    # Use the real Git merge-base export, not a fabricated baseline.
    from code_health.repository import exported_revision

    with exported_revision(repo, old) as before:
        result = sd.collect(repo, Path("."), {f"left.{suffix}"}, old, before)
    assert len(result.one_sided_edits) == 1
    split = result.one_sided_edits[0]
    assert split.before.path == split.changed_hunk.path == f"left.{suffix}"
    assert split.remaining.path == f"right.{suffix}"
    assert split.changed_hunk.start == split.changed_hunk.end == 3


def test_intentional_deletion_move_and_bilateral_change_have_no_split(repo):
    from code_health.repository import exported_revision

    for n in ("a", "b"):
        (repo / f"{n}.py").write_text(SOURCES["py"])
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "before")
    old = git(repo, "rev-parse", "HEAD")
    with exported_revision(repo, old) as before:
        (repo / "a.py").write_text("")
        assert not sd.collect(repo, Path("."), {"a.py"}, old, before).one_sided_edits
        for n in ("a", "b"):
            (repo / f"{n}.py").write_text(
                SOURCES["py"].replace("return fallback", "return different")
            )
        assert not sd.collect(
            repo, Path("."), {"a.py", "b.py"}, old, before
        ).one_sided_edits
        (repo / "a.py").write_text(SOURCES["py"])
        (repo / "b.py").write_text(SOURCES["py"])
        git(repo, "mv", "b.py", "z.py")
        assert not sd.collect(
            repo, Path("."), {"b.py", "z.py"}, old, before
        ).one_sided_edits


def test_literal_examples_are_not_proof_of_semantics(repo):
    for file in ("a.py", "b.py"):
        (repo / file).write_text('EXAMPLE = """\n' + SOURCES["py"] + '\n"""\n')
    git(repo, "add", ".")
    # Intentionally document a lexical false positive, not an executable decision.
    assert len(sd.collect(repo, Path("."), None).matches) == 1


def test_scope_and_git_quoted_names(repo):
    (repo / "inside").mkdir()
    for file in ("inside/one.py", "inside/bébé.py", "outside.py"):
        (repo / file).write_text(SOURCES["py"])
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "before")
    old = git(repo, "rev-parse", "HEAD")
    (repo / "inside/bébé.py").write_text(
        SOURCES["py"].replace("return fallback", "return alternate")
    )
    from code_health.repository import exported_revision

    with exported_revision(repo, old) as before:
        result = sd.collect(repo, Path("inside"), set(), old, before)
    assert result.reviewed_files == 2
    assert [s.remaining.path for s in result.one_sided_edits] == ["inside/one.py"]
