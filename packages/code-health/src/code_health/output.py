"""Stable JSON and concise Markdown output."""

from __future__ import annotations

import json

from code_health.models import Report


def render_json(report: Report) -> str:
    """Render stable machine-readable output."""
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


def render_markdown(report: Report) -> str:
    """Render a compact evidence report for a human reviewer."""
    lines = [
        "# Code Health Evidence",
        "",
        f"- Repository: `{report.repository}`",
        f"- Repository root: `{report.repository_root}`",
        f"- Scope: `{report.scope}`",
        f"- Revision: `{report.revision}`",
        f"- Mode: `{report.mode}`",
        f"- Status: `{report.status}`",
        f"- Churn window: {report.churn_days} days",
        f"- Working tree: {'dirty' if report.working_tree_paths else 'clean'}",
    ]
    if report.working_tree_paths:
        lines.append(f"- Working-tree paths: {len(report.working_tree_paths)}")
    if report.base:
        lines.append(f"- Base: `{report.base}`")
    if report.baseline_revision:
        lines.append(f"- Baseline revision: `{report.baseline_revision}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Findings: {report.summary['findings']}",
            f"- Findings in changed files: {report.summary['changed_findings']}",
            f"- New / worsened: {report.summary['new']} / {report.summary['worsened']}",
            f"- Improved / resolved: {report.summary['improved']} / {report.summary['resolved']}",
            "",
            "## Highest-signal findings",
            "",
        ]
    )
    if not report.findings:
        lines.append("No selected analyzer findings.")
    for finding in report.findings[:10]:
        value = (
            f"{finding.value}/{finding.threshold}"
            if finding.value is not None and finding.threshold is not None
            else finding.message
        )
        marker = "changed" if finding.changed else "existing"
        symbol = f" `{finding.symbol}`" if finding.symbol else ""
        lines.append(
            f"- `{finding.path}:{finding.line}`{symbol} — "
            f"{finding.tool}:{finding.rule} {finding.metric} {value}; "
            f"churn={finding.churn}; {marker}"
        )
    changed_deltas = [delta for delta in report.deltas if delta.status != "unchanged"]
    if changed_deltas:
        lines.extend(["", "## Representative deltas", ""])
        for delta in changed_deltas[:10]:
            evidence = delta.after_finding or delta.before_finding
            assert evidence is not None
            before = "absent" if delta.before is None else str(delta.before)
            after = "absent" if delta.after is None else str(delta.after)
            symbol = f" `{delta.symbol}`" if delta.symbol else ""
            lines.append(
                f"- {delta.status}: `{delta.path}:{evidence.line}`{symbol} — "
                f"{evidence.tool}:{evidence.rule} {delta.metric} {before} → {after}; "
                f"threshold={evidence.threshold}"
            )
    unavailable = [tool for tool in report.tools if tool.status != "ok"]
    if unavailable or report.unavailable_metrics:
        lines.extend(["", "## Evidence gaps", ""])
        for tool in unavailable:
            lines.append(f"- {tool.tool}: {tool.status} — {tool.detail}")
        for metric in report.unavailable_metrics:
            lines.append(f"- {metric['metric']}: unavailable — {metric['reason']}")
    return "\n".join(lines)
