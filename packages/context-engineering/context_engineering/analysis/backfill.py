"""Extract provenance-preserving local Git evidence for contract backfill."""

from __future__ import annotations

import datetime
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit, urlunsplit

from ..domain.evidence import (
    EvidenceBoundary,
    EvidenceCompleteness,
    EvidenceLimitation,
    EvidenceScopeKind,
)
from ..domain.finding import Finding, Severity
from ..domain.result import AnalysisResult
from ..infra.git import git_root, resolve_commit
from ..infra.git_evidence import (
    CompleteHistoryRecord,
    CompletePathChange,
    EvidenceBudget,
    communicate_bounded,
    read_complete_history,
    read_history,
)

_FIELD = "\x1f"
_DESIGN_PATH_RE = re.compile(
    r"(?:^|/)(?:docs?|agent[-_]?docs?|design[-_]?docs?|architecture|design|decisions?|adrs?)(?:/|$)|"
    r"(?:^|/)(?:SPEC|README|CHANGELOG)\.md$",
    re.IGNORECASE,
)
_SUBJECT_SIGNALS = (
    "adopt",
    "architecture",
    "conversion",
    "design",
    "lifecycle",
    "migrate",
    "pipeline",
    "refactor",
    "replace",
    "supersede",
)
_SENSITIVE_SUBJECT_RE = re.compile(
    r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|password|secret|api[-_ ]?key|access[-_ ]?token)",
    re.IGNORECASE,
)
_SENSITIVE_PATH_RE = re.compile(
    r"(?:^|/)(?:\.env(?:\.|$)|credentials?|secrets?|private[-_]?keys?)(?:/|\.|$)",
    re.IGNORECASE,
)
_LEAD_WEIGHTS = {
    "design-artifact": 5,
    "renamed-or-copied-path": 4,
    "deleted-path": 3,
    "architecture-subject-lead": 2,
    "merged-pr-subject-lead": 1,
}
_MAX_HIGH_SIGNAL_COMMITS = 100


class QuickHistoryRecord(TypedDict):
    commit: str
    date: str
    subject: str
    paths: list[str]


class LeadRecord(CompleteHistoryRecord):
    reasons: list[str]


@dataclass
class _EvidenceMeter:
    budget: EvidenceBudget
    records: int = 0
    paths: int = 0
    bytes: int = 0
    subprocesses: int = 0

    def consume(
        self,
        *,
        records: int = 0,
        paths: int = 0,
        bytes_read: int = 0,
        subprocesses: int = 0,
    ) -> str | None:
        self.records += records
        self.paths += paths
        self.bytes += bytes_read
        self.subprocesses += subprocesses
        if self.records > self.budget.max_records:
            return "evidence exceeds the configured record ceiling"
        if self.paths > self.budget.max_paths:
            return "evidence exceeds the configured path ceiling"
        if self.bytes > self.budget.max_bytes:
            return "evidence exceeds the configured byte ceiling"
        if self.subprocesses > self.budget.max_subprocesses:
            return "evidence exceeds the configured subprocess ceiling"
        return None

    def to_dict(self) -> dict[str, int]:
        return {
            "records": self.records,
            "paths": self.paths,
            "bytes": self.bytes,
            "subprocesses": self.subprocesses,
        }


def _history(
    repo: Path,
    module: Path,
    cutoff: str,
    max_commits: int,
) -> tuple[list[QuickHistoryRecord], str | None]:
    relative = module.relative_to(repo).as_posix()
    records, error = read_history(
        repo,
        cutoff=cutoff,
        relative_path=relative,
        max_count=max_commits,
    )
    return [
        {
            "commit": record.commit,
            "date": record.date,
            "subject": record.subject,
            "paths": list(record.paths),
        }
        for record in records
    ], error


def _complete_history(
    repo: Path,
    cutoff: str,
) -> tuple[list[CompleteHistoryRecord], str | None]:
    records, _counts, error = read_complete_history(repo, cutoff=cutoff)
    return records, error


def _git_value(
    repo: Path, *args: str, meter: _EvidenceMeter | None = None
) -> tuple[str | None, str | None]:
    command = ["git", *args]
    if meter is None:
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
        if result.returncode != 0:
            return None, result.stderr.strip() or f"git {' '.join(args)} exited {result.returncode}"
        return result.stdout.strip(), None
    remaining = meter.budget.max_bytes - meter.bytes
    if remaining < 0:
        return None, "evidence exceeds the configured byte ceiling"
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return None, f"could not run Git: {exc}"
    stdout, stderr, transport_error = communicate_bounded(process, max_bytes=remaining)
    ceiling_error = meter.consume(
        bytes_read=len(stdout) + len(stderr),
        subprocesses=1,
    )
    if transport_error is not None or ceiling_error is not None:
        error = transport_error or ceiling_error
        assert error is not None
        return None, (
            "evidence exceeds the configured byte ceiling" if "ceiling" in error else error
        )
    if process.returncode != 0:
        diagnostic = os.fsdecode(stderr).strip()
        return None, diagnostic or f"git {' '.join(args)} exited {process.returncode}"
    return os.fsdecode(stdout).strip(), None


def _empty_commit_record(
    repo: Path,
    commit: str,
    meter: _EvidenceMeter | None = None,
) -> tuple[CompleteHistoryRecord | None, str | None]:
    value, error = _git_value(
        repo,
        "show",
        "-s",
        f"--format=%H{_FIELD}%aI{_FIELD}%s{_FIELD}%P{_FIELD}END",
        commit,
        meter=meter,
    )
    if error or value is None:
        return None, error
    fields = value.split(_FIELD, 4)
    if len(fields) != 5 or fields[4] != "END":
        return None, f"git show returned malformed metadata for {commit}"
    return {
        "commit": fields[0],
        "date": fields[1][:10],
        "subject": fields[2],
        "parents": fields[3].split() if fields[3] else [],
        "changes": [],
    }, None


def _path_is_within(path: str, prefix: str) -> bool:
    return prefix == "." or path == prefix or path.startswith(prefix + "/")


def _relative_path(path: str, prefix: str) -> str:
    if prefix == ".":
        return path
    if path == prefix:
        return ""
    return path[len(prefix) + 1 :]


def _prefix_before_suffix(path: str, suffix: str) -> str | None:
    if not suffix:
        return path
    if path == suffix:
        return "."
    marker = "/" + suffix
    if not path.endswith(marker):
        return None
    return path[: -len(marker)] or "."


def _tree_paths(
    repo: Path,
    commit: str,
    prefix: str,
    meter: _EvidenceMeter | None = None,
) -> tuple[list[str], str | None]:
    args = ["git", "ls-tree", "-r", "-z", "--name-only", commit, "--"]
    if prefix != ".":
        args.append(prefix)
    if meter is None:
        result = subprocess.run(args, cwd=repo, capture_output=True)
        if result.returncode != 0:
            diagnostic = os.fsdecode(result.stderr).strip()
            return [], diagnostic or f"git ls-tree exited {result.returncode}"
        return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path], None
    remaining = meter.budget.max_bytes - meter.bytes
    if remaining < 0:
        return [], "evidence exceeds the configured byte ceiling"
    try:
        process = subprocess.Popen(args, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return [], f"could not run Git: {exc}"
    stdout, stderr, transport_error = communicate_bounded(process, max_bytes=remaining)
    if transport_error is not None:
        meter.consume(bytes_read=len(stdout) + len(stderr), subprocesses=1)
        return [], (
            "evidence exceeds the configured byte ceiling"
            if "ceiling" in transport_error
            else transport_error
        )
    paths = [os.fsdecode(path) for path in stdout.split(b"\0") if path]
    ceiling_error = meter.consume(
        paths=len(paths),
        bytes_read=len(stdout) + len(stderr),
        subprocesses=1,
    )
    if ceiling_error:
        return [], ceiling_error
    if process.returncode != 0:
        diagnostic = os.fsdecode(stderr).strip()
        return [], diagnostic or f"git ls-tree exited {process.returncode}"
    return paths, None


def _exact_previous_prefix(
    repo: Path,
    record: CompleteHistoryRecord,
    current_prefix: str,
    parent: str,
    incoming_renames: list[CompletePathChange],
    meter: _EvidenceMeter | None = None,
) -> tuple[str | None, str | None]:
    candidates: set[str] = set()
    for change in incoming_renames:
        relative = _relative_path(change["path"], current_prefix)
        candidate = _prefix_before_suffix(change["old_path"], relative)
        if candidate is None:
            return None, "rename pairs do not preserve one target-relative path layout"
        candidates.add(candidate)
    if len(candidates) != 1:
        return None, "rename pairs originate from multiple module prefixes"
    previous_prefix = candidates.pop()
    previous_paths, previous_error = _tree_paths(repo, parent, previous_prefix, meter)
    current_parent_paths, current_parent_error = _tree_paths(repo, parent, current_prefix, meter)
    current_paths, current_error = _tree_paths(
        repo, str(record["commit"]), current_prefix, meter
    )
    tree_error = previous_error or current_parent_error or current_error
    if tree_error:
        return None, tree_error
    if not previous_paths or current_parent_paths or not current_paths:
        return None, "tree state does not establish an exact whole-module move"
    rename_pairs = {(change["old_path"], change["path"]) for change in incoming_renames}
    deleted_paths = {change["path"] for change in record["changes"] if change["status"] == "D"}
    for previous_path in previous_paths:
        relative = _relative_path(previous_path, previous_prefix)
        expected_path = (
            relative if current_prefix == "." else f"{current_prefix}/{relative}".rstrip("/")
        )
        if (
            previous_path,
            expected_path,
        ) not in rename_pairs and previous_path not in deleted_paths:
            return None, "not every prior module path is accounted for by the move"
    return previous_prefix, None


def _module_history(
    repo: Path,
    records: list[CompleteHistoryRecord],
    current_prefix: str,
    cutoff: str,
    meter: _EvidenceMeter | None = None,
) -> tuple[list[CompleteHistoryRecord], list[dict[str, str]], str | None]:
    if current_prefix == ".":
        return records, [], None
    cutoff_paths, cutoff_error = _tree_paths(repo, cutoff, current_prefix, meter)
    if cutoff_error:
        return [], [], cutoff_error
    if not cutoff_paths:
        return [], [], f"target path does not exist at cutoff: {current_prefix}"

    selected: list[CompleteHistoryRecord] = []
    lineage: list[dict[str, str]] = []
    active_prefix = current_prefix
    for record in reversed(records):
        changes = record["changes"]
        parents = record["parents"]
        relevant_changes = [
            change
            for change in changes
            if (
                _path_is_within(str(change["path"]), active_prefix)
                or (
                    "old_path" in change and _path_is_within(str(change["old_path"]), active_prefix)
                )
            )
        ]
        if not relevant_changes:
            continue

        parent_states: list[bool] = []
        for parent in parents:
            parent_paths, parent_error = _tree_paths(repo, str(parent), active_prefix, meter)
            if parent_error:
                return [], [], parent_error
            parent_states.append(bool(parent_paths))
        if parents and not any(parent_states):
            incoming_renames = [
                change
                for change in relevant_changes
                if str(change["status"]).startswith("R")
                and "old_path" in change
                and _path_is_within(str(change["path"]), active_prefix)
                and not _path_is_within(str(change["old_path"]), active_prefix)
            ]
            if incoming_renames:
                if len(parents) != 1:
                    return [], [], "module move occurs at a multi-parent commit"
                previous_prefix, lineage_error = _exact_previous_prefix(
                    repo,
                    record,
                    active_prefix,
                    str(parents[0]),
                    incoming_renames,
                    meter,
                )
                if lineage_error or previous_prefix is None:
                    return [], [], lineage_error or "module lineage is ambiguous"
                lineage_changes = [
                    change
                    for change in changes
                    if (
                        _path_is_within(str(change["path"]), active_prefix)
                        or _path_is_within(str(change["path"]), previous_prefix)
                        or (
                            "old_path" in change
                            and (
                                _path_is_within(str(change["old_path"]), active_prefix)
                                or _path_is_within(str(change["old_path"]), previous_prefix)
                            )
                        )
                    )
                ]
                selected.append({**record, "changes": lineage_changes})
                lineage.append(
                    {
                        "commit": str(record["commit"]),
                        "old_path": previous_prefix,
                        "path": active_prefix,
                    }
                )
                active_prefix = previous_prefix
                continue
            out_of_scope_deletions = [
                change
                for change in changes
                if str(change["status"]) == "D"
                and not _path_is_within(str(change["path"]), active_prefix)
            ]
            if out_of_scope_deletions:
                return (
                    [],
                    [],
                    "target appears after out-of-scope deletions without a proven rename",
                )
            selected.append({**record, "changes": relevant_changes})
            break
        selected.append({**record, "changes": relevant_changes})
    return list(reversed(selected)), list(reversed(lineage)), None


def _signal_reasons(record: CompleteHistoryRecord) -> list[str]:
    reasons: set[str] = set()
    changes = record["changes"]
    for change in changes:
        status = str(change["status"])
        paths = [str(change["path"])]
        if "old_path" in change:
            paths.append(str(change["old_path"]))
        if status == "D":
            reasons.add("deleted-path")
        if status.startswith(("R", "C")):
            reasons.add("renamed-or-copied-path")
        if any(_DESIGN_PATH_RE.search(path) for path in paths):
            reasons.add("design-artifact")
    subject = str(record["subject"]).casefold()
    if any(token in subject for token in _SUBJECT_SIGNALS):
        reasons.add("architecture-subject-lead")
    if re.search(r"\(#\d+\)\s*$", subject):
        reasons.add("merged-pr-subject-lead")
    return sorted(reasons)


def _historical_design_artifacts(
    records: list[CompleteHistoryRecord],
) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    for record in records:
        changes = record["changes"]
        for change in changes:
            paths = [str(change["path"])]
            if "old_path" in change:
                paths.append(str(change["old_path"]))
            if not any(_DESIGN_PATH_RE.search(path) for path in paths):
                continue
            artifacts.append(
                {
                    "status": change["status"],
                    "path": change["path"],
                    **({"old_path": change["old_path"]} if "old_path" in change else {}),
                    "provenance": {
                        "source": "local-git",
                        "commit": record["commit"],
                        "paths": paths,
                    },
                }
            )
    return artifacts


def _rank_leads(records: list[CompleteHistoryRecord]) -> list[LeadRecord]:
    leads: list[LeadRecord] = [
        {**record, "reasons": reasons} for record in records if (reasons := _signal_reasons(record))
    ]
    return sorted(
        leads,
        key=lambda record: (
            -sum(_LEAD_WEIGHTS[reason] for reason in record["reasons"]),
            str(record["date"]),
            str(record["commit"]),
        ),
    )[:_MAX_HIGH_SIGNAL_COMMITS]


def _remote(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    remote = result.stdout.strip()
    parts = urlsplit(remote)
    if parts.scheme == "file" or Path(remote).is_absolute():
        return None
    if not parts.scheme or not parts.netloc:
        scp_match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", remote)
        if scp_match is None:
            return None
        return f"{scp_match.group(1)}:{scp_match.group(2)}"
    safe_netloc = parts.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parts.scheme, safe_netloc, parts.path, "", ""))


def _analysis_target(module: Path, repo: Path | None, *, publish_safe: bool) -> str:
    if not publish_safe:
        return str(module)
    if repo is None:
        return module.name
    identity = _remote(repo) or repo.name
    relative = module.relative_to(repo).as_posix()
    return identity if relative == "." else f"{identity}:{relative}"


def _sensitivity_flags(records: list[CompleteHistoryRecord]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for record in records:
        commit = str(record["commit"])
        if _SENSITIVE_SUBJECT_RE.search(str(record["subject"])):
            flags.append({"commit": commit, "field": "subject", "reason": "sensitive-text-pattern"})
        for change in record["changes"]:
            for field in ("path", "old_path"):
                value = change.get(field)
                if value is not None and _SENSITIVE_PATH_RE.search(str(value)):
                    flags.append(
                        {
                            "commit": commit,
                            "field": field,
                            "reason": "sensitive-path-pattern",
                        }
                    )
    return flags


def _publish_safe_leads(records: list[LeadRecord]) -> list[dict[str, object]]:
    return [
        {
            "commit": record["commit"],
            "date": record["date"],
            "reasons": record["reasons"],
        }
        for record in records
    ]


def _quick_sensitivity_flags(records: list[QuickHistoryRecord]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for record in records:
        commit = str(record["commit"])
        if _SENSITIVE_SUBJECT_RE.search(str(record["subject"])):
            flags.append({"commit": commit, "field": "subject", "reason": "sensitive-text-pattern"})
        paths = record["paths"]
        if any(_SENSITIVE_PATH_RE.search(str(path)) for path in paths):
            flags.append({"commit": commit, "field": "paths", "reason": "sensitive-path-pattern"})
    return flags


def analyze(
    module: Path,
    *,
    cutoff: str = "HEAD",
    max_commits: int | None = None,
    quick: bool = False,
    publish_safe: bool = False,
) -> AnalysisResult:
    module = module.resolve()
    mode = "quick" if quick else "complete-picture"
    reconstructed = datetime.datetime.now(datetime.UTC).date().isoformat()
    repo = git_root(module)
    result_target = _analysis_target(module, repo, publish_safe=publish_safe)
    empty_data: dict[str, object] = {
        "mode": mode,
        "cutoff": cutoff,
        "reconstruction_date": reconstructed,
        "github_enrichment": "not-requested",
        "publication": {
            "mode": "publish-safe" if publish_safe else "local-evidence",
            "durable_doc_propagation_requires_approval": True,
        },
        "claims": [],
        "claims_by_kind": {"verified_fact": [], "inference": [], "contradiction": []},
        "proposed_spec": None,
        "adr_candidates": [],
        "write_performed": False,
    }
    if not quick and max_commits is not None:
        message = "max_commits requires quick mode"
        finding = Finding(
            result_target,
            0,
            Severity.ERROR,
            "context-backfill-max-commits-requires-quick",
            message,
        )
        data = {
            **empty_data,
            "deterministic_errors": [{"code": "max-commits-requires-quick", "message": message}],
        }
        return AnalysisResult(result_target, data, [finding])
    history_limit = 100 if max_commits is None else max_commits
    if history_limit < 0:
        message = "max_commits must be non-negative"
        finding = Finding(
            result_target,
            0,
            Severity.ERROR,
            "context-backfill-invalid-max-commits",
            message,
        )
        data = {
            **empty_data,
            "deterministic_errors": [{"code": "invalid-max-commits", "message": message}],
        }
        return AnalysisResult(result_target, data, [finding])
    if repo is None:
        finding = Finding(
            result_target,
            0,
            Severity.ERROR,
            "context-backfill-not-git",
            "Target is not in a Git repository",
        )
        data = {
            **empty_data,
            "deterministic_errors": [{"code": "not-a-git-repository", "message": finding.message}],
        }
        return AnalysisResult(result_target, data, [finding])
    resolved_cutoff, error = resolve_commit(repo, cutoff)
    if error:
        finding = Finding(
            result_target,
            0,
            Severity.ERROR,
            "context-backfill-invalid-cutoff",
            error,
        )
        data = {
            **empty_data,
            "deterministic_errors": [{"code": "invalid-cutoff", "message": error}],
        }
        return AnalysisResult(result_target, data, [finding])
    assert resolved_cutoff is not None
    if not quick:
        relative = module.relative_to(repo).as_posix()
        scope_kind = EvidenceScopeKind.REPOSITORY if relative == "." else EvidenceScopeKind.MODULE
        budget = EvidenceBudget()
        meter = _EvidenceMeter(budget)
        cutoff_tree, tree_error = _git_value(
            repo, "rev-parse", f"{resolved_cutoff}^{{tree}}", meter=meter
        )
        shallow, shallow_error = _git_value(
            repo, "rev-parse", "--is-shallow-repository", meter=meter
        )
        state_error = tree_error or shallow_error
        if state_error or shallow not in {"true", "false"}:
            message = state_error or f"Git returned an invalid shallow state: {shallow!r}"
            finding = Finding(
                result_target,
                0,
                Severity.ERROR,
                "context-backfill-unknown-history",
                message,
            )
            boundary = EvidenceBoundary(
                completeness=EvidenceCompleteness.UNKNOWN,
                scope_kind=scope_kind,
                scope_path=relative,
                cutoff_sha=resolved_cutoff,
                cutoff_tree=cutoff_tree,
                limitations=(EvidenceLimitation("history-state-unknown", message),),
            )
            return AnalysisResult(
                result_target,
                {
                    **empty_data,
                    "cutoff": resolved_cutoff,
                    "requested_cutoff": cutoff,
                    "cutoff_tree": cutoff_tree,
                    "evidence_boundary": boundary.to_dict(),
                    "raw_evidence": [],
                    "deterministic_errors": [{"code": "history-state-unknown", "message": message}],
                },
                [finding],
            )
        if shallow == "true":
            message = "Local Git history is shallow; repository genesis cannot be proven"
            finding = Finding(
                result_target,
                0,
                Severity.ERROR,
                "context-backfill-incomplete-history",
                message,
            )
            boundary = EvidenceBoundary(
                completeness=EvidenceCompleteness.INCOMPLETE,
                scope_kind=scope_kind,
                scope_path=relative,
                cutoff_sha=resolved_cutoff,
                cutoff_tree=cutoff_tree,
                limitations=(EvidenceLimitation("shallow-repository", message),),
            )
            return AnalysisResult(
                result_target,
                {
                    **empty_data,
                    "cutoff": resolved_cutoff,
                    "requested_cutoff": cutoff,
                    "cutoff_tree": cutoff_tree,
                    "evidence_boundary": boundary.to_dict(),
                    "raw_evidence": [],
                    "deterministic_errors": [{"code": "shallow-repository", "message": message}],
                },
                [finding],
            )
        remaining_budget = EvidenceBudget(
            max_records=budget.max_records - meter.records,
            max_paths=budget.max_paths - meter.paths,
            max_bytes=budget.max_bytes - meter.bytes,
            max_subprocesses=budget.max_subprocesses - meter.subprocesses,
        )
        repository_history, history_counts, error = read_complete_history(
            repo,
            cutoff=resolved_cutoff,
            budget=remaining_budget,
        )
        meter_error = meter.consume(
            records=history_counts.records,
            paths=history_counts.paths,
            bytes_read=history_counts.bytes,
            subprocesses=history_counts.subprocesses,
        )
        error = error or meter_error
        if error:
            resource_limited = "ceiling" in error
            code = (
                "context-backfill-resource-ceiling"
                if resource_limited
                else "context-backfill-git-error"
            )
            finding = Finding(result_target, 0, Severity.ERROR, code, error)
            boundary = EvidenceBoundary(
                completeness=EvidenceCompleteness.INCOMPLETE,
                scope_kind=scope_kind,
                scope_path=relative,
                cutoff_sha=resolved_cutoff,
                cutoff_tree=cutoff_tree,
                limitations=(
                    EvidenceLimitation(
                        "resource-ceiling" if resource_limited else "history-read-failed",
                        error,
                    ),
                ),
            )
            data = {
                **empty_data,
                "cutoff": resolved_cutoff,
                "requested_cutoff": cutoff,
                "evidence_boundary": boundary.to_dict(),
                "resource_counts": meter.to_dict(),
                "raw_evidence": [],
                "deterministic_errors": [
                    {
                        "code": "resource-ceiling" if resource_limited else "git-history-error",
                        "message": error,
                    }
                ],
            }
            return AnalysisResult(result_target, data, [finding])
        genesis, genesis_error = _git_value(
            repo,
            "rev-list",
            "--max-parents=0",
            "--reverse",
            resolved_cutoff,
            meter=meter,
        )
        identity_error = genesis_error
        if identity_error:
            finding = Finding(
                result_target,
                0,
                Severity.ERROR,
                "context-backfill-git-error",
                identity_error,
            )
            return AnalysisResult(
                result_target,
                {
                    **empty_data,
                    "cutoff": resolved_cutoff,
                    "requested_cutoff": cutoff,
                    "deterministic_errors": [
                        {"code": "git-identity-error", "message": identity_error}
                    ],
                },
                [finding],
            )
        genesis_commits = genesis.splitlines() if genesis else []
        present_commits = {str(record["commit"]) for record in repository_history}
        for genesis_commit in reversed(genesis_commits):
            if genesis_commit in present_commits:
                continue
            genesis_record, genesis_record_error = _empty_commit_record(
                repo, genesis_commit, meter
            )
            if genesis_record_error is None and genesis_record is not None:
                genesis_record_error = meter.consume(records=1)
            if genesis_record_error or genesis_record is None:
                message = genesis_record_error or "Git did not return genesis metadata"
                resource_limited = "ceiling" in message
                finding = Finding(
                    result_target,
                    0,
                    Severity.ERROR,
                    (
                        "context-backfill-resource-ceiling"
                        if resource_limited
                        else "context-backfill-git-error"
                    ),
                    message,
                )
                return AnalysisResult(
                    result_target,
                    {
                        **empty_data,
                        "cutoff": resolved_cutoff,
                        "requested_cutoff": cutoff,
                        "resource_counts": meter.to_dict(),
                        "deterministic_errors": [
                            {
                                "code": (
                                    "resource-ceiling"
                                    if resource_limited
                                    else "git-genesis-error"
                                ),
                                "message": message,
                            }
                        ],
                    },
                    [finding],
                )
            repository_history.insert(0, genesis_record)
        history, target_path_lineage, lineage_error = _module_history(
            repo,
            repository_history,
            relative,
            resolved_cutoff,
            meter,
        )
        if lineage_error:
            resource_limited = "ceiling" in lineage_error
            boundary = EvidenceBoundary(
                completeness=EvidenceCompleteness.INCOMPLETE,
                scope_kind=scope_kind,
                scope_path=relative,
                cutoff_sha=resolved_cutoff,
                cutoff_tree=cutoff_tree,
                repository_roots=tuple(genesis_commits),
                limitations=(
                    EvidenceLimitation(
                        "resource-ceiling" if resource_limited else "module-lineage-ambiguous",
                        lineage_error,
                    ),
                ),
            )
            finding = Finding(
                result_target,
                0,
                Severity.ERROR,
                (
                    "context-backfill-resource-ceiling"
                    if resource_limited
                    else "context-backfill-module-lineage-ambiguous"
                ),
                lineage_error,
            )
            return AnalysisResult(
                result_target,
                {
                    **empty_data,
                    "cutoff": resolved_cutoff,
                    "requested_cutoff": cutoff,
                    "cutoff_tree": cutoff_tree,
                    "genesis": genesis_commits[0] if genesis_commits else None,
                    "genesis_commits": genesis_commits,
                    "repository_genesis": genesis_commits[0] if genesis_commits else None,
                    "repository_genesis_commits": genesis_commits,
                    "target_first_evidenced_commit": None,
                    "target_path_at_cutoff": relative,
                    "target_path_lineage": [],
                    "evidence_boundary": boundary.to_dict(),
                    "resource_counts": meter.to_dict(),
                    "raw_evidence": [],
                    "deterministic_errors": [
                        {
                            "code": (
                                "resource-ceiling"
                                if resource_limited
                                else "module-lineage-ambiguous"
                            ),
                            "message": lineage_error,
                        }
                    ],
                },
                [finding],
            )
        high_signal = _rank_leads(history)
        repository = _remote(repo) or repo.name
        sensitivity_flags = _sensitivity_flags(history)
        boundary = EvidenceBoundary(
            completeness=EvidenceCompleteness.COMPLETE,
            scope_kind=scope_kind,
            scope_path=relative,
            cutoff_sha=resolved_cutoff,
            cutoff_tree=cutoff_tree,
            repository_roots=tuple(genesis_commits),
        )
        return AnalysisResult(
            target=result_target,
            data={
                **empty_data,
                "cutoff": resolved_cutoff,
                "requested_cutoff": cutoff,
                "cutoff_tree": cutoff_tree,
                "genesis": genesis_commits[0] if genesis_commits else None,
                "genesis_commits": genesis_commits,
                "repository_genesis": genesis_commits[0] if genesis_commits else None,
                "repository_genesis_commits": genesis_commits,
                "target_first_evidenced_commit": (str(history[0]["commit"]) if history else None),
                "target_path_at_cutoff": relative,
                "target_path_lineage": target_path_lineage,
                "evidence_boundary": boundary.to_dict(),
                "repository": repository,
                "resource_counts": meter.to_dict(),
                "sensitivity_flags": sensitivity_flags,
                "sources": [
                    {
                        "source": "local-git",
                        "repository": repository,
                        "cutoff": resolved_cutoff,
                        "scope": (
                            "genesis-through-cutoff"
                            if relative == "."
                            else "target-lineage-through-cutoff"
                        ),
                    }
                ],
                "raw_evidence": [] if publish_safe else history,
                "high_signal_commits": (
                    _publish_safe_leads(high_signal) if publish_safe else high_signal
                ),
                "historical_design_artifacts": (
                    [] if publish_safe else _historical_design_artifacts(history)
                ),
                "publish_safe_omissions": (
                    ["commit subjects", "historical paths", "design-artifact paths"]
                    if publish_safe
                    else []
                ),
                "verified_facts": [],
                "inferences": [],
                "contradictions_and_supersessions": [],
                "phase_timeline": [],
                "decision_inventory": [],
                "adr_promotion_suggestions": [],
                "rejected_candidates": [],
                "evidence_gaps": [],
                "proposed_spec": None,
                "proposed_docs": {"architecture": None, "project_evolution": None},
                "merged_pr_evidence": {
                    "optional": True,
                    "availability": "unknown",
                    "used": False,
                    "items": [],
                },
                "deterministic_errors": [],
            },
        )
    history, error = _history(repo, module, resolved_cutoff, history_limit)
    if error:
        finding = Finding(result_target, 0, Severity.ERROR, "context-backfill-git-error", error)
        data = {
            **empty_data,
            "cutoff": resolved_cutoff,
            "requested_cutoff": cutoff,
            "deterministic_errors": [{"code": "git-history-error", "message": error}],
        }
        return AnalysisResult(result_target, data, [finding])
    repository = _remote(repo) or repo.name
    boundary = EvidenceBoundary(
        completeness=EvidenceCompleteness.BOUNDED,
        scope_kind=EvidenceScopeKind.RECENT_HISTORY,
        scope_path=module.relative_to(repo).as_posix(),
        cutoff_sha=resolved_cutoff,
        cutoff_tree=None,
        limitations=(
            EvidenceLimitation(
                "quick-mode",
                "Quick mode intentionally limits local Git history",
            ),
        ),
    )
    claims = [
        {
            "kind": "verified_fact",
            "claim": (
                f"Commit {record['commit'][:12]} ({record['subject']}) changed "
                f"{', '.join(record['paths'])}."
            ),
            "effective_date": record["date"],
            "reconstruction_date": reconstructed,
            "provenance": [
                {
                    "source": "local-git",
                    "repository": repository,
                    "commit": record["commit"],
                    "paths": record["paths"],
                }
            ],
        }
        for record in history
    ]
    sensitivity_flags = _quick_sensitivity_flags(history)
    if publish_safe:
        claims = []
    return AnalysisResult(
        target=result_target,
        data={
            **empty_data,
            "cutoff": resolved_cutoff,
            "requested_cutoff": cutoff,
            "repository": repository,
            "resource_counts": {
                "records": len(history),
                "paths": sum(len(record["paths"]) for record in history),
                "bytes": None,
                "subprocesses": 1,
            },
            "sensitivity_flags": sensitivity_flags,
            "publish_safe_omissions": (
                ["commit subjects", "historical paths"] if publish_safe else []
            ),
            "evidence_boundary": boundary.to_dict(),
            "claims": claims,
            "claims_by_kind": {
                "verified_fact": list(range(len(claims))),
                "inference": [],
                "contradiction": [],
            },
            "deterministic_errors": [],
        },
    )
