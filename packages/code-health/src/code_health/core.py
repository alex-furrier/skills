"""Repository analysis orchestration."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from code_health.analyzers import ADAPTERS
from code_health.models import Finding, MetricDelta, Report, ToolStatus
from code_health.repository import (
    changed_paths,
    churn_by_path,
    default_base,
    detect_languages,
    discover_root,
    exported_revision,
    merge_base,
    repository_identity,
    revision,
    size_metrics,
    working_tree_paths,
)

# Most metrics are counts or complexity scores where higher values are worse.
# Maintainability index is the sole current inverse metric.
LOWER_IS_WORSE_METRICS = frozenset({"maintainability-index"})

UNAVAILABLE_METRICS = [
    {
        "metric": "duplication",
        "reason": "No clone detector is implemented in version 1.",
    },
    {
        "metric": "dependency-graph",
        "reason": "Dependency entropy and propagation cost are not implemented.",
    },
    {
        "metric": "single-use-symbols",
        "reason": "Cross-language decomposition analysis is not implemented.",
    },
]


def _paths_in_scope(paths: set[str], scope: Path) -> set[str]:
    if scope == Path("."):
        return paths
    return {path for path in paths if Path(path) == scope or Path(path).is_relative_to(scope)}


def _prepare_adapters(
    root: Path, target: Path, languages: list[str], temporary: Path
) -> tuple[dict[str, object], list[ToolStatus]]:
    """Resolve optional tools once from the candidate workspace for both revisions."""
    contexts: dict[str, object] = {}
    statuses: list[ToolStatus] = []
    for language in languages:
        prepare, _adapter = ADAPTERS[language]
        if prepare is None:
            continue
        try:
            context, status = prepare(root, temporary, target)
        except RuntimeError as error:
            context = None
            status = ToolStatus(
                {"typescript": "eslint", "go": "golangci-lint"}.get(language, language),
                "error",
                f"{language} preparation failed: {error}",
            )
        contexts[language] = context
        statuses.append(status)
    return contexts, statuses


def _analyze_prepared(
    target: Path, root: Path, languages: list[str], contexts: dict[str, object]
) -> tuple[list[Finding], list[ToolStatus]]:
    findings: list[Finding] = []
    tools: list[ToolStatus] = []
    if not languages:
        return [], [ToolStatus("source-analyzer", "unavailable", "no supported source files found")]
    for language in languages:
        prepare, adapter = ADAPTERS[language]
        try:
            if prepare is None:
                adapter_findings, status = adapter(target, root)
            else:
                adapter_findings, status = adapter(target, root, contexts.get(language))
        except RuntimeError as error:
            adapter_findings = []
            status = ToolStatus(
                {"typescript": "eslint", "go": "golangci-lint"}.get(language, language),
                "error",
                f"{language} analysis failed: {error}",
            )
        findings.extend(adapter_findings)
        tools.append(status)
    return findings, tools


def _decorate(findings: list[Finding], changed: set[str], churn: dict[str, int]) -> list[Finding]:
    return sorted(
        (
            replace(
                finding,
                changed=finding.path in changed,
                churn=churn.get(finding.path, 0),
            )
            for finding in findings
        ),
        key=lambda item: (
            not item.changed,
            -item.churn,
            item.path,
            item.line,
            item.rule,
        ),
    )


class DeltaEvidenceGap(RuntimeError):
    """An analyzer's findings cannot be matched safely across snapshots."""

    def __init__(self, tool: str, detail: str) -> None:
        super().__init__(detail)
        self.tool = tool
        self.detail = detail


def _deltas(current: list[Finding], baseline: list[Finding]) -> list[MetricDelta]:
    def index(findings: list[Finding], label: str) -> dict[tuple[str, str, str, str], Finding]:
        indexed: dict[tuple[str, str, str, str], Finding] = {}
        for finding in findings:
            if finding.key in indexed:
                raise DeltaEvidenceGap(
                    finding.tool,
                    f"duplicate {label} finding identity {finding.key!r}; "
                    "analyzer symbols must be collision-safe"
                )
            indexed[finding.key] = finding
        return indexed

    def structural_key(finding: Finding) -> tuple[str, str, str, str] | None:
        """Return ESLint's owner/name identity, excluding its snapshot signature."""
        if finding.tool != "eslint" or "@signature:" not in finding.symbol:
            return None
        owner_name, _signature = finding.symbol.split("@signature:", 1)
        return (finding.path, owner_name, finding.metric, finding.rule)

    def delta(before_finding: Finding | None, after_finding: Finding | None) -> MetricDelta:
        finding = after_finding or before_finding
        assert finding is not None
        before = before_finding.value if before_finding else None
        after = after_finding.value if after_finding else None
        if before_finding is None:
            status = "new"
        elif after_finding is None:
            status = "resolved"
        elif before is None or after is None:
            status = "unchanged"
        else:
            higher_is_worse = finding.metric not in LOWER_IS_WORSE_METRICS
            if after > before:
                status = "worsened" if higher_is_worse else "improved"
            elif after < before:
                status = "improved" if higher_is_worse else "worsened"
            else:
                status = "unchanged"
        return MetricDelta(
            finding.path,
            finding.symbol or f"line:{finding.line}",
            finding.metric,
            finding.rule,
            before,
            after,
            status,
            before_finding,
            after_finding,
        )

    current_by_key = index(current, "current")
    baseline_by_key = index(baseline, "baseline")
    pairs: list[tuple[Finding | None, Finding | None]] = []
    # A declaration with an unchanged signature is unambiguously the same one.
    exact_keys = set(current_by_key) & set(baseline_by_key)
    pairs.extend((baseline_by_key[key], current_by_key[key]) for key in exact_keys)
    unmatched_current = [
        finding for key, finding in current_by_key.items() if key not in exact_keys
    ]
    unmatched_baseline = [
        finding for key, finding in baseline_by_key.items() if key not in exact_keys
    ]

    # Signature edits intentionally change the per-snapshot identity. Reconcile a
    # sole remaining declaration by its structural owner/name only; multiple
    # remaining declarations are an evidence gap rather than false deltas.
    current_structural: dict[tuple[str, str, str, str], list[Finding]] = {}
    baseline_structural: dict[tuple[str, str, str, str], list[Finding]] = {}
    for finding in unmatched_current:
        if key := structural_key(finding):
            current_structural.setdefault(key, []).append(finding)
    for finding in unmatched_baseline:
        if key := structural_key(finding):
            baseline_structural.setdefault(key, []).append(finding)
    reconciled_current: set[tuple[str, str, str, str]] = set()
    reconciled_baseline: set[tuple[str, str, str, str]] = set()
    for key in set(current_structural) & set(baseline_structural):
        after = current_structural[key]
        before = baseline_structural[key]
        if len(after) == len(before) == 1:
            pairs.append((before[0], after[0]))
            reconciled_current.add(after[0].key)
            reconciled_baseline.add(before[0].key)
        else:
            owner_name = key[1]
            raise DeltaEvidenceGap(
                "eslint",
                f"cannot reconcile changed TypeScript declarations for {owner_name!r}",
            )

    pairs.extend(
        (None, finding) for finding in unmatched_current if finding.key not in reconciled_current
    )
    pairs.extend(
        (finding, None) for finding in unmatched_baseline if finding.key not in reconciled_baseline
    )
    return sorted(
        (delta(before_finding, after_finding) for before_finding, after_finding in pairs),
        key=lambda item: (item.path, item.symbol, item.metric, item.rule, item.status),
    )


def _verified_deltas(
    current: list[Finding],
    baseline: list[Finding],
    current_tools: list[ToolStatus],
    baseline_tools: list[ToolStatus],
) -> tuple[list[MetricDelta], list[ToolStatus]]:
    """Compare usable analyzer evidence and report unsafe cross-snapshot matches."""
    unavailable = {tool.tool for tool in [*current_tools, *baseline_tools] if tool.status != "ok"}
    tools = sorted({finding.tool for finding in [*current, *baseline]} - unavailable)
    deltas: list[MetricDelta] = []
    gaps: list[ToolStatus] = []
    for tool in tools:
        try:
            deltas.extend(
                _deltas(
                    [finding for finding in current if finding.tool == tool],
                    [finding for finding in baseline if finding.tool == tool],
                )
            )
        except DeltaEvidenceGap as error:
            gaps.append(ToolStatus(f"{error.tool}-delta", "unavailable", error.detail))
    return sorted(
        deltas,
        key=lambda item: (item.path, item.symbol, item.metric, item.rule, item.status),
    ), gaps


def _status(tools: list[ToolStatus]) -> str:
    return "ok" if tools and all(tool.status == "ok" for tool in tools) else "partial"


def analyze(
    path: Path,
    *,
    mode: str,
    base: str | None,
    churn_days: int,
) -> Report:
    """Analyze one repository snapshot or baseline diff."""
    root = discover_root(path)
    candidate = path.resolve()
    target = candidate.parent if candidate.is_file() else candidate
    try:
        scope_path = target.relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"analysis path {target} is outside repository {root}") from error
    candidate_languages = detect_languages(target)
    selected_base = base
    baseline_revision: str | None = None
    working_paths = _paths_in_scope(working_tree_paths(root), scope_path)
    changed: set[str] = set()
    if mode == "diff":
        selected_base = base or default_base(root)
        baseline_revision = merge_base(root, selected_base)
        changed = changed_paths(root, baseline_revision)
    churn = churn_by_path(root, churn_days)
    with tempfile.TemporaryDirectory(prefix="code-health-tools-") as temporary:
        baseline_languages: list[str] = []
        if mode == "diff" and baseline_revision is not None:
            with exported_revision(root, baseline_revision) as exported:
                baseline_target = exported / scope_path
                if baseline_target.exists():
                    baseline_languages = detect_languages(baseline_target)
                languages = list(dict.fromkeys([*candidate_languages, *baseline_languages]))
                contexts, preparation_tools = _prepare_adapters(
                    root, target, languages, Path(temporary)
                )
                findings, tools = _analyze_prepared(target, root, candidate_languages, contexts)
                decorated = _decorate(findings, changed, churn)
                baseline_findings, baseline_tools = (
                    _analyze_prepared(baseline_target, exported, baseline_languages, contexts)
                    if baseline_target.exists()
                    else ([], [])
                )
        else:
            languages = candidate_languages
            contexts, preparation_tools = _prepare_adapters(
                root, target, languages, Path(temporary)
            )
            findings, tools = _analyze_prepared(target, root, languages, contexts)
            decorated = _decorate(findings, changed, churn)
            baseline_findings, baseline_tools = [], []
        analysis_tools = tools
        if mode == "diff":
            deltas, delta_tools = _verified_deltas(
                decorated, baseline_findings, analysis_tools, baseline_tools
            )
        else:
            deltas, delta_tools = [], []
        tools = [*preparation_tools, *analysis_tools, *delta_tools]
        tools.extend(
            ToolStatus(f"{tool.tool}-baseline", tool.status, tool.detail, tool.command)
            for tool in baseline_tools
        )
    summary = {
        "findings": len(decorated),
        "changed_findings": sum(finding.changed for finding in decorated),
        "new": sum(delta.status == "new" for delta in deltas),
        "worsened": sum(delta.status == "worsened" for delta in deltas),
        "improved": sum(delta.status == "improved" for delta in deltas),
        "resolved": sum(delta.status == "resolved" for delta in deltas),
    }
    return Report(
        version=1,
        mode=mode,
        repository=repository_identity(root),
        scope=scope_path.as_posix() or ".",
        repository_root=str(root),
        revision=revision(root),
        base=selected_base,
        baseline_revision=baseline_revision,
        churn_days=churn_days,
        working_tree_paths=sorted(working_paths),
        status=_status(tools),
        languages=candidate_languages,
        size=size_metrics(target),
        summary=summary,
        findings=decorated,
        deltas=deltas,
        tools=tools,
        unavailable_metrics=list(UNAVAILABLE_METRICS),
    )
