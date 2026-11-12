#!/usr/bin/env python3
"""Collect exact Git diff shape and render owner-supplied conceptual groups."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

DESCRIPTION = "Collect deterministic Git change shape without external diff or text conversion."
ATTRIBUTES = (
    "linguist-generated",
    "linguist-vendored",
    "linguist-documentation",
    "diff",
    "text",
)
LOCKFILES = {
    "bun.lock",
    "bun.lockb",
    "cargo.lock",
    "composer.lock",
    "flake.lock",
    "gemfile.lock",
    "go.sum",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}
MANIFESTS = {
    "cargo.toml",
    "composer.json",
    "deno.json",
    "deno.jsonc",
    "flake.nix",
    "gemfile",
    "go.mod",
    "package.json",
    "plugin.json",
    "pyproject.toml",
}
CONFIG_NAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "dockerfile",
    "makefile",
    "mise.toml",
    "ruff.toml",
}


def _git(
    repo: Path,
    argv: list[str],
    *,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
) -> bytes:
    completed = subprocess.run(
        argv,
        cwd=repo,
        input=input_bytes,
        capture_output=True,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{' '.join(argv)} failed ({completed.returncode}): {stderr}")
    return completed.stdout


def _path_text(path: bytes) -> str:
    return os.fsdecode(path)


def parse_raw(data: bytes) -> list[dict[str, Any]]:
    tokens = data.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    records: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        metadata = tokens[index]
        index += 1
        fields = metadata.split()
        if len(fields) != 5 or not fields[0].startswith(b":"):
            raise ValueError(f"malformed raw diff record: {metadata!r}")
        if index >= len(tokens):
            raise ValueError("raw diff record has no path")
        status = fields[4].decode("ascii")
        first_path = tokens[index]
        index += 1
        old_path: bytes | None = None
        path = first_path
        if status.startswith(("R", "C")):
            if index >= len(tokens):
                raise ValueError("rename/copy raw record has no destination path")
            old_path = first_path
            path = tokens[index]
            index += 1
        records.append(
            {
                "old_mode": fields[0][1:].decode("ascii"),
                "new_mode": fields[1].decode("ascii"),
                "old_oid": fields[2].decode("ascii"),
                "new_oid": fields[3].decode("ascii"),
                "status": status,
                "old_path_bytes": old_path,
                "path_bytes": path,
            }
        )
    return records


def parse_numstat(data: bytes) -> list[dict[str, Any]]:
    tokens = data.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    records: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        header = tokens[index]
        index += 1
        fields = header.split(b"\t", 2)
        if len(fields) != 3:
            raise ValueError(f"malformed numstat record: {header!r}")
        additions_raw, deletions_raw, path = fields
        old_path: bytes | None = None
        if path == b"":
            if index + 1 >= len(tokens):
                raise ValueError("rename/copy numstat record lacks paths")
            old_path = tokens[index]
            path = tokens[index + 1]
            index += 2
        binary = additions_raw == b"-" and deletions_raw == b"-"
        if binary:
            additions = deletions = None
        else:
            try:
                additions = int(additions_raw)
                deletions = int(deletions_raw)
            except ValueError as error:
                raise ValueError(f"invalid numstat counts: {header!r}") from error
        records.append(
            {
                "old_path_bytes": old_path,
                "path_bytes": path,
                "additions": additions,
                "deletions": deletions,
                "binary": binary,
            }
        )
    return records


def join_records(
    raw_records: list[dict[str, Any]], stat_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if len(raw_records) != len(stat_records):
        raise ValueError(
            f"raw/numstat record count differs: {len(raw_records)} != {len(stat_records)}"
        )
    joined: list[dict[str, Any]] = []
    for raw, stat in zip(raw_records, stat_records, strict=True):
        if raw["path_bytes"] != stat["path_bytes"]:
            raise ValueError("raw/numstat destination paths differ")
        if raw["old_path_bytes"] != stat["old_path_bytes"]:
            raise ValueError("raw/numstat source paths differ")
        joined.append({**raw, **stat})
    return joined


def _segments(path: str) -> tuple[str, ...]:
    return tuple(segment.lower() for segment in PurePosixPath(path).parts)


def _test_role(path: str) -> str | None:
    segments = _segments(path)
    name = PurePosixPath(path).name.lower()
    # A Markdown correctness specification is documentation, not executable tests.
    if name == "spec.md":
        return "docs"
    if any(segment in {"test", "tests", "spec", "specs"} for segment in segments) or re.search(
        r"(?:^|[_.-])(test|spec)(?:[_.-]|$)", name
    ):
        return "test"
    if "docs" in segments or name.endswith((".md", ".mdx", ".rst", ".adoc")):
        return "docs"
    return None


def _attribute_boolean(value: str | None) -> bool | None:
    if value is None or value == "unspecified":
        return None
    lowered = value.lower()
    if lowered in {"set", "true"}:
        return True
    if lowered in {"unset", "false"}:
        return False
    return None


def classify_file(path_bytes: bytes, attrs: dict[str, str]) -> dict[str, Any]:
    path = _path_text(path_bytes)
    lowered = path.lower()
    name = PurePosixPath(lowered).name
    segments = _segments(lowered)
    role = _test_role(path)

    def classified(
        bucket: str,
        kind: str | None,
        role_hint: str | None,
        source: str = "reviewed_fallback",
    ) -> dict[str, Any]:
        return {
            "bucket": bucket,
            "supporting_kind": kind,
            "role_hint": role_hint,
            "source": source,
        }

    if name in LOCKFILES or name.endswith((".lock", ".lockb")):
        return classified("supporting", "lockfile", role)
    vendored = _attribute_boolean(attrs.get("linguist-vendored"))
    generated = _attribute_boolean(attrs.get("linguist-generated"))
    documentation = _attribute_boolean(attrs.get("linguist-documentation"))
    if vendored is True:
        return classified("supporting", "vendored", role, "gitattributes")
    if generated is True:
        return classified("supporting", "generated", role, "gitattributes")
    if documentation is True:
        return classified("supporting", "docs", None, "gitattributes")
    documentation_unset = documentation is False
    generated_unset = generated is False
    vendored_unset = vendored is False
    if name.endswith(".ipynb"):
        return classified("supporting", "notebook", role)
    if any(
        segment in {"fixture", "fixtures", "testdata", "test-data", "snapshots", "golden"}
        for segment in segments
    ):
        return classified("supporting", "fixture", role)
    if role == "test":
        return classified("supporting", "test", None)
    document_suffixes = (".md", ".mdx", ".rst", ".adoc")
    if not documentation_unset and ("docs" in segments or name.endswith(document_suffixes)):
        return classified("supporting", "docs", None)
    if not generated_unset and any(
        segment in {"generated", "dist", "build", "coverage"} for segment in segments
    ):
        return classified("supporting", "generated", role)
    if not vendored_unset and any(
        segment in {"vendor", "vendored", "third_party", "third-party"} for segment in segments
    ):
        return classified("supporting", "vendored", role)
    if name in MANIFESTS or name.startswith("brewfile"):
        return classified("supporting", "manifest", None)
    if (
        name in CONFIG_NAMES
        or name.startswith(".")
        and name.endswith(("rc", ".yml", ".yaml", ".toml"))
        or name.endswith((".ini", ".cfg", ".conf"))
        or "config" in segments
        and not name.endswith((".py", ".js", ".ts", ".go", ".rs", *document_suffixes))
        or any(segment in {".github", "provisioning", "deploy", "ops"} for segment in segments)
    ):
        return classified("supporting", "config", role)
    if documentation_unset or generated_unset or vendored_unset:
        return classified("core", None, None, "gitattributes_veto")
    return classified("core", None, None)


def _parse_attributes(data: bytes) -> dict[bytes, dict[str, str]]:
    tokens = data.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    if len(tokens) % 3:
        raise ValueError("git check-attr returned malformed NUL records")
    result: dict[bytes, dict[str, str]] = defaultdict(dict)
    for index in range(0, len(tokens), 3):
        path, attribute, value = tokens[index : index + 3]
        result[path][attribute.decode("ascii")] = value.decode("utf-8", errors="surrogateescape")
    return dict(result)


@contextmanager
def _isolated_bare_repository(repo: Path) -> Iterator[tuple[Path, dict[str, str]]]:
    object_directory = Path(
        _path_text(
            _git(
                repo,
                ["git", "rev-parse", "--path-format=absolute", "--git-path", "objects"],
            ).rstrip(b"\n")
        )
    )
    object_format = _git(repo, ["git", "rev-parse", "--show-object-format"]).decode("ascii").strip()
    isolated_env = os.environ.copy()
    isolated_env.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
        }
    )
    with tempfile.TemporaryDirectory(prefix="pr-change-shape-git-") as temporary:
        temporary_root = Path(temporary)
        template = temporary_root / "template"
        template.mkdir()
        isolated_repo = temporary_root / "repo.git"
        _git(
            repo,
            [
                "git",
                "init",
                "--bare",
                "--quiet",
                f"--object-format={object_format}",
                f"--template={template}",
                str(isolated_repo),
            ],
            env=isolated_env,
        )
        alternates = isolated_repo / "objects/info/alternates"
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.write_text(f"{object_directory}\n", encoding="utf-8")
        yield isolated_repo, isolated_env


def _attributes_for_tree(
    repo: Path,
    isolated_repo: Path,
    isolated_env: dict[str, str],
    tree: str,
    paths: list[bytes],
) -> dict[bytes, dict[str, str]]:
    if not paths:
        return {}
    argv = [
        "git",
        f"--git-dir={isolated_repo}",
        "-c",
        f"core.attributesFile={os.devnull}",
        "check-attr",
        f"--source={tree}",
        "-z",
        "--stdin",
        *ATTRIBUTES,
    ]
    output = _git(
        repo,
        argv,
        input_bytes=b"\0".join(paths) + b"\0",
        env=isolated_env,
    )
    return _parse_attributes(output)


def _tree_numstat(
    repo: Path,
    isolated_repo: Path,
    isolated_env: dict[str, str],
    argv: list[str],
    attribute_tree: str,
) -> list[dict[str, Any]]:
    env = isolated_env.copy()
    env["GIT_ATTR_SOURCE"] = attribute_tree
    isolated_argv = [
        "git",
        f"--git-dir={isolated_repo}",
        "-c",
        f"core.attributesFile={os.devnull}",
        *argv[1:],
    ]
    return parse_numstat(_git(repo, isolated_argv, env=env))


def _select_numstat_records(
    raw_records: list[dict[str, Any]],
    base_records: list[dict[str, Any]],
    head_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # Validate both views before selecting the committed attribute tree for each path.
    join_records(raw_records, base_records)
    join_records(raw_records, head_records)
    return [
        base_stat if raw["status"].startswith("D") else head_stat
        for raw, base_stat, head_stat in zip(raw_records, base_records, head_records, strict=True)
    ]


def collect_change_shape(repo: Path, base: str, head: str) -> dict[str, Any]:
    repo = repo.resolve()
    merge_base = _git(repo, ["git", "merge-base", base, head]).decode().strip()
    head_oid = _git(repo, ["git", "rev-parse", f"{head}^{{commit}}"]).decode().strip()
    range_spec = f"{base}...{head}"
    raw_argv = [
        "git",
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--raw",
        "-z",
        "-M",
        merge_base,
        head_oid,
    ]
    numstat_argv = [
        "git",
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--numstat",
        "-z",
        "-M",
        merge_base,
        head_oid,
    ]
    with _isolated_bare_repository(repo) as (isolated_repo, isolated_env):
        isolated_raw_argv = [
            "git",
            f"--git-dir={isolated_repo}",
            "-c",
            f"core.attributesFile={os.devnull}",
            *raw_argv[1:],
        ]
        raw_records = parse_raw(_git(repo, isolated_raw_argv, env=isolated_env))
        base_numstat = _tree_numstat(repo, isolated_repo, isolated_env, numstat_argv, merge_base)
        head_numstat = _tree_numstat(repo, isolated_repo, isolated_env, numstat_argv, head_oid)
        records = join_records(
            raw_records,
            _select_numstat_records(raw_records, base_numstat, head_numstat),
        )

        base_paths = [
            record["path_bytes"] for record in records if record["status"].startswith("D")
        ]
        head_paths = [
            record["path_bytes"] for record in records if not record["status"].startswith("D")
        ]
        base_attrs = _attributes_for_tree(repo, isolated_repo, isolated_env, merge_base, base_paths)
        head_attrs = _attributes_for_tree(repo, isolated_repo, isolated_env, head_oid, head_paths)

    files: list[dict[str, Any]] = []
    totals = {
        "additions": 0,
        "deletions": 0,
        "textual_changed_line_events": 0,
        "binary_files": 0,
        "submodule_changes": 0,
        "renames": 0,
        "type_changes": 0,
    }
    for record in records:
        deleted = record["status"].startswith("D")
        attribute_tree = merge_base if deleted else head_oid
        attrs = (base_attrs if deleted else head_attrs).get(record["path_bytes"], {})
        classification = classify_file(record["path_bytes"], attrs)
        submodule = record["old_mode"] == "160000" or record["new_mode"] == "160000"
        type_change = record["status"].startswith("T")
        binary = bool(record["binary"])
        additions = record["additions"]
        deletions = record["deletions"]
        if submodule:
            additions = deletions = None
        if isinstance(additions, int) and isinstance(deletions, int):
            events = additions + deletions
            totals["additions"] += additions
            totals["deletions"] += deletions
            totals["textual_changed_line_events"] += events
        else:
            events = None
        if binary:
            totals["binary_files"] += 1
        if submodule:
            totals["submodule_changes"] += 1
        if record["status"].startswith("R"):
            totals["renames"] += 1
        if type_change:
            totals["type_changes"] += 1
        files.append(
            {
                "path": _path_text(record["path_bytes"]),
                "old_path": (
                    _path_text(record["old_path_bytes"])
                    if record["old_path_bytes"] is not None
                    else None
                ),
                "status": record["status"],
                "old_mode": record["old_mode"],
                "new_mode": record["new_mode"],
                "additions": additions,
                "deletions": deletions,
                "textual_changed_line_events": events,
                "special": {
                    "binary": binary,
                    "submodule": submodule,
                    "rename": record["status"].startswith("R"),
                    "type_change": type_change,
                },
                "attributes": {"tree": attribute_tree, "values": attrs},
                "classification": classification,
                "conceptual_group": None,
            }
        )
    files.sort(key=lambda item: item["path"].encode("utf-8", errors="surrogateescape"))
    return {
        "schema_version": 1,
        "git": {
            "base": base,
            "head": head,
            "merge_base": merge_base,
            "head_oid": head_oid,
            "range": range_spec,
            "raw_argv": raw_argv,
            "numstat_argv": numstat_argv,
            "attribute_sources": {"base": merge_base, "head": head_oid},
            "external_diff": False,
            "textconv": False,
        },
        "files": files,
        "totals": totals,
        "public_breakdown_required": totals["textual_changed_line_events"] > 500,
        "interpretation": (
            "Counts are Git additions plus deletions. Modified lines can count twice. "
            "They describe diff shape, not effort, risk, quality, or readiness."
        ),
    }


def requires_public_breakdown(shape: dict[str, Any]) -> bool:
    return int(shape["totals"]["textual_changed_line_events"]) > 500


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _file_cell(path: str) -> str:
    escaped = html.escape(path, quote=False)
    escaped = escaped.replace("|", "&#124;").replace("\r", "&#13;").replace("\n", "&#10;")
    return f"<code>{escaped}</code>"


def _count_cell(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _count_noun(count: int, singular: str) -> str:
    noun = singular if count == 1 else f"{singular}s"
    return f"{count} {noun}"


def _file_count(count: int) -> str:
    return _count_noun(count, "file")


def _append_core_details(
    lines: list[str],
    core_files: list[dict[str, Any]],
    groups: dict[str, str],
    group_totals: dict[str, dict[str, int]],
) -> None:
    if not core_files:
        return
    core_events = sum(int(item["textual_changed_line_events"] or 0) for item in core_files)
    lines.extend(
        [
            "",
            "<details>",
            (
                f"<summary>Core changes: {core_events:,} changed-line events "
                f"across {_file_count(len(core_files))}</summary>"
            ),
            "",
            "| Conceptual group | File | Additions | Deletions | Changed-line events |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    ordered_groups = sorted(group_totals, key=lambda label: (-group_totals[label]["events"], label))
    for label in ordered_groups:
        members = sorted(
            (item for item in core_files if groups[item["path"]].strip() == label),
            key=lambda item: (-int(item["textual_changed_line_events"] or 0), item["path"]),
        )
        for item in members:
            lines.append(
                f"| {_escape_cell(label)} | {_file_cell(item['path'])} | "
                f"{_count_cell(item['additions'])} | {_count_cell(item['deletions'])} | "
                f"{_count_cell(item['textual_changed_line_events'])} |"
            )
        values = group_totals[label]
        lines.append(
            f"| **{_escape_cell(label)} total** | **{_file_count(len(members))}** | "
            f"**{values['additions']:,}** | **{values['deletions']:,}** | "
            f"**{values['events']:,}** |"
        )
    lines.extend(["", "</details>"])


def _append_supporting_details(
    lines: list[str],
    supporting_files: list[dict[str, Any]],
    supporting: dict[str, dict[str, int]],
) -> None:
    if not supporting_files:
        return
    supporting_events = sum(value["events"] for value in supporting.values())
    lines.extend(
        [
            "",
            "<details>",
            (
                f"<summary>Supporting changes: {supporting_events:,} changed-line events "
                f"across {_file_count(len(supporting_files))}</summary>"
            ),
            "",
            "| Supporting kind | Files | Additions | Deletions | Changed-line events |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    ordered_kinds = sorted(supporting, key=lambda kind: (-supporting[kind]["events"], kind))
    for kind in ordered_kinds:
        values = supporting[kind]
        lines.append(
            f"| {_escape_cell(kind)} | {values['files']} | {values['additions']:,} | "
            f"{values['deletions']:,} | {values['events']:,} |"
        )
    lines.extend(
        [
            "",
            "#### Supporting files",
            "",
            "| Supporting kind | File | Additions | Deletions | Changed-line events |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for kind in ordered_kinds:
        members = sorted(
            (
                item
                for item in supporting_files
                if (item["classification"]["supporting_kind"] or "other") == kind
            ),
            key=lambda item: (-int(item["textual_changed_line_events"] or 0), item["path"]),
        )
        for item in members:
            lines.append(
                f"| {_escape_cell(kind)} | {_file_cell(item['path'])} | "
                f"{_count_cell(item['additions'])} | {_count_cell(item['deletions'])} | "
                f"{_count_cell(item['textual_changed_line_events'])} |"
            )
        values = supporting[kind]
        lines.append(
            f"| **{_escape_cell(kind)} total** | **{_file_count(len(members))}** | "
            f"**{values['additions']:,}** | **{values['deletions']:,}** | "
            f"**{values['events']:,}** |"
        )
    lines.extend(["", "</details>"])


def render_markdown(shape: dict[str, Any], groups: dict[str, str]) -> str:
    core_files = [item for item in shape["files"] if item["classification"]["bucket"] == "core"]
    core_paths = {item["path"] for item in core_files}
    supplied_paths = set(groups)
    extra = supplied_paths - core_paths
    if extra:
        raise ValueError(f"unknown or supporting path in conceptual groups: {sorted(extra)!r}")
    missing = core_paths - supplied_paths
    if missing:
        raise ValueError(f"missing conceptual group for core paths: {sorted(missing)!r}")
    labels = {label.strip() for label in groups.values() if label.strip()}
    if len(labels) != len({label.strip() for label in groups.values()}):
        raise ValueError("conceptual group labels must be non-empty")
    if len(labels) > 5:
        raise ValueError("use at most five core conceptual groups")

    group_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"additions": 0, "deletions": 0, "events": 0}
    )
    for item in core_files:
        label = groups[item["path"]].strip()
        if not label:
            raise ValueError(f"empty conceptual group for {item['path']!r}")
        values = group_totals[label]
        if item["textual_changed_line_events"] is None:
            continue
        values["additions"] += item["additions"]
        values["deletions"] += item["deletions"]
        values["events"] += item["textual_changed_line_events"]

    supporting: dict[str, dict[str, int]] = defaultdict(
        lambda: {"additions": 0, "deletions": 0, "events": 0, "files": 0}
    )
    supporting_files = [
        item for item in shape["files"] if item["classification"]["bucket"] == "supporting"
    ]
    for item in supporting_files:
        kind = item["classification"]["supporting_kind"] or "other"
        supporting[kind]["files"] += 1
        if item["textual_changed_line_events"] is not None:
            supporting[kind]["additions"] += item["additions"]
            supporting[kind]["deletions"] += item["deletions"]
            supporting[kind]["events"] += item["textual_changed_line_events"]

    total = shape["totals"]
    supporting_additions = sum(value["additions"] for value in supporting.values())
    supporting_deletions = sum(value["deletions"] for value in supporting.values())
    supporting_events = sum(value["events"] for value in supporting.values())
    lines = [
        (
            f"**Change shape:** {total['textual_changed_line_events']:,} Git textual "
            "changed-line events."
        ),
        (
            "Counts are additions plus deletions, so modified lines can count twice. "
            "They describe diff shape, not effort, risk, quality, review time, or readiness."
        ),
        "",
        "| Conceptual group | Additions | Deletions | Changed-line events |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, values in sorted(
        group_totals.items(), key=lambda pair: (-pair[1]["events"], pair[0])
    ):
        lines.append(
            f"| {_escape_cell(label)} | {values['additions']:,} | {values['deletions']:,} | "
            f"{values['events']:,} |"
        )
    if supporting:
        lines.append(
            f"| Supporting changes | {supporting_additions:,} | "
            f"{supporting_deletions:,} | {supporting_events:,} |"
        )
    lines.append(
        f"| **Total** | **{total['additions']:,}** | **{total['deletions']:,}** | "
        f"**{total['textual_changed_line_events']:,}** |"
    )
    _append_core_details(lines, core_files, groups, group_totals)
    _append_supporting_details(lines, supporting_files, supporting)
    special = []
    if total.get("binary_files"):
        special.append(_count_noun(total["binary_files"], "binary file"))
    if total.get("submodule_changes"):
        special.append(_count_noun(total["submodule_changes"], "submodule change"))
    if total.get("type_changes"):
        special.append(_count_noun(total["type_changes"], "type change"))
    if special:
        lines.extend(
            ["", "Special changes with no invented line count: " + ", ".join(special) + "."]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--groups-json", type=Path)
    parser.add_argument("--markdown", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    shape = collect_change_shape(args.repo, args.base, args.head)
    if args.markdown:
        if args.groups_json is None:
            raise SystemExit("--markdown requires --groups-json with model-owned core groups")
        groups = json.loads(args.groups_json.read_text())
        if not isinstance(groups, dict) or not all(
            isinstance(path, str) and isinstance(label, str) for path, label in groups.items()
        ):
            raise SystemExit("--groups-json must contain a string-to-string object")
        print(render_markdown(shape, groups))
    else:
        print(json.dumps(shape, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
