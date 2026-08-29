"""Discover and validate portable SPEC.md and ADR contracts."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ..analysis.context_layout import discover
from ..domain.finding import Finding, Severity
from ..domain.result import AnalysisResult
from ..infra.markdown import mask_invisible_markdown
from ..infra.yaml_frontmatter import parse_frontmatter

SPEC_SECTIONS = (
    "Summary",
    "Goals / Non-Goals",
    "Requirements",
    "Interfaces & Contracts",
    "Invariants",
    "Acceptance",
)
LEGACY_SPEC_SECTIONS = {"purpose", "scope", "invariants", "interfaces", "validation"}
ADR_STATUSES = {"proposed", "accepted", "deprecated", "superseded", "rejected"}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+\.md(?:#[^)]+)?)\)", re.IGNORECASE)
_NORMATIVE_STATEMENT_RE = re.compile(
    r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)?[^\n]*\S\s+(?:MUST|SHOULD|MAY)\s+\S+"
)
_LEGACY_MIGRATION_HINT = (
    "Migrate Purpose to Summary; split Scope into Goals / Non-Goals; rewrite "
    "observable obligations under Requirements with MUST, SHOULD, or MAY; "
    "rename Interfaces to Interfaces & Contracts; keep Invariants; and replace "
    "Validation with Acceptance."
)


def _finding(path: Path, root: Path, code: str, message: str, hint: str | None = None) -> Finding:
    return Finding(
        file=path.relative_to(root).as_posix() if path != root else ".",
        line=1,
        severity=Severity.ERROR,
        code=code,
        message=message,
        hint=hint,
    )


def _spec_sections(content: str) -> list[str]:
    return [
        match.group(2).strip().casefold()
        for match in _HEADING_RE.finditer(content)
        if match.group(1) == "##"
    ]


def _section_body(content: str, section: str) -> str | None:
    matches = [match for match in _HEADING_RE.finditer(content) if match.group(1) == "##"]
    for index, match in enumerate(matches):
        if match.group(2).strip().casefold() != section.casefold():
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        return content[match.end() : end]
    return None


def _read(path: Path, root: Path) -> tuple[str | None, list[Finding]]:
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError) as error:
        return None, [
            _finding(
                path,
                root,
                "contract-read-failed",
                f"Contract file could not be read as UTF-8: {error}",
            )
        ]


def _metadata(content: str) -> tuple[dict[str, str], str, set[str]]:
    frontmatter, body = parse_frontmatter(content)
    metadata: dict[str, str] = {}
    duplicates: set[str] = set()
    if frontmatter:
        metadata.update(
            {
                key.casefold().replace("-", "_"): str(value).strip()
                for key, value in frontmatter.items()
            }
        )
    visible = mask_invisible_markdown(body)
    second_level = re.search(r"^##\s+", visible, re.MULTILINE)
    preamble = visible[: second_level.start()] if second_level else visible
    for line in preamble.splitlines():
        match = re.match(r"^(Status|Date|Superseded[ _-]by):\s*(.+?)\s*$", line, re.IGNORECASE)
        if match:
            key = match.group(1).casefold().replace(" ", "_").replace("-", "_")
            if key in metadata:
                duplicates.add(key)
            metadata[key] = match.group(2)
    return metadata, body, duplicates


def _section_code(section: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", section.casefold()).strip("-")


def _has_substantive_content(body: str) -> bool:
    visible = re.sub(r"[\s#>*_`~\[\](){}.+\-]+", " ", body).strip()
    return bool(re.search(r"[A-Za-z0-9]", visible))


def _check_spec(spec: Path, root: Path) -> list[Finding]:
    content, findings = _read(spec, root)
    if content is None:
        return findings
    _frontmatter, body = parse_frontmatter(content)
    visible_content = mask_invisible_markdown(body)
    headings = list(_HEADING_RE.finditer(visible_content))
    titles = [match for match in headings if match.group(1) == "#"]
    sections = _spec_sections(visible_content)
    section_set = set(sections)
    canonical_sections = [section.casefold() for section in SPEC_SECTIONS]
    if not titles:
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-missing-title",
                "SPEC.md needs one level-one title",
            )
        )
    elif len(titles) > 1:
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-multiple-titles",
                "SPEC.md needs exactly one level-one title",
            )
        )
    if LEGACY_SPEC_SECTIONS.issubset(section_set):
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-legacy-profile",
                "SPEC.md uses the retired Purpose/Scope/Interfaces/Validation profile",
                _LEGACY_MIGRATION_HINT,
            )
        )
    for section in SPEC_SECTIONS:
        if section.casefold() not in section_set:
            findings.append(
                _finding(
                    spec,
                    root,
                    f"contract-spec-missing-{section.casefold().replace(' ', '-')}",
                    f"SPEC.md is missing the required '{section}' section",
                )
            )
    noncanonical = [section for section in sections if section not in canonical_sections]
    duplicate_sections = sorted(
        section for section in canonical_sections if sections.count(section) > 1
    )
    if duplicate_sections:
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-duplicate-section",
                "SPEC.md repeats a canonical second-level section: "
                + ", ".join(duplicate_sections),
            )
        )
    if noncanonical:
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-noncanonical-section",
                "SPEC.md contains a noncanonical second-level section: " + ", ".join(noncanonical),
                "Keep only Summary; Goals / Non-Goals; Requirements; "
                "Interfaces & Contracts; Invariants; and Acceptance as second-level sections.",
            )
        )
    if (
        not noncanonical
        and not duplicate_sections
        and section_set == set(canonical_sections)
        and sections != canonical_sections
    ):
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-section-order",
                "SPEC.md sections are not in the canonical order",
                "Order sections as Summary; Goals / Non-Goals; Requirements; "
                "Interfaces & Contracts; Invariants; and Acceptance.",
            )
        )
    requirements = _section_body(visible_content, "Requirements")
    for section in SPEC_SECTIONS:
        section_body = _section_body(visible_content, section)
        if section_body is not None and not _has_substantive_content(section_body):
            findings.append(
                _finding(
                    spec,
                    root,
                    f"contract-spec-empty-{_section_code(section)}",
                    f"SPEC.md '{section}' section has no substantive visible content",
                )
            )
    if requirements is not None and not _NORMATIVE_STATEMENT_RE.search(requirements):
        findings.append(
            _finding(
                spec,
                root,
                "contract-spec-requirements-not-normative",
                "SPEC.md Requirements do not contain a normative obligation",
                "State each obligation with MUST, SHOULD, or MAY.",
            )
        )
    return findings


def _adr_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.glob("*.md")
        if path.name.casefold() not in {"readme.md", "index.md"}
    )


def _target_is_within_root(target: Path, root: Path) -> bool:
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _check_supersession(adr: Path, root: Path, metadata: dict[str, str]) -> list[Finding]:
    status = metadata.get("status", "").casefold()
    superseded_by = metadata.get("superseded_by")
    if status == "superseded" and not superseded_by:
        return [
            _finding(
                adr,
                root,
                "contract-adr-supersession-target-missing",
                "A superseded ADR must name its replacement with 'Superseded by:'",
            )
        ]
    if superseded_by:
        target = (adr.parent / superseded_by.split("#", 1)[0]).resolve()
        if not _target_is_within_root(target, root):
            return [
                _finding(
                    adr,
                    root,
                    "contract-adr-supersession-target-outside-root",
                    f"Supersession target leaves the validated root: {superseded_by}",
                )
            ]
        if not target.is_file():
            return [
                _finding(
                    adr,
                    root,
                    "contract-adr-supersession-target-missing",
                    f"Supersession target does not exist: {superseded_by}",
                )
            ]
    return []


def _check_adr_links(adr: Path, root: Path, content: str) -> list[Finding]:
    findings: list[Finding] = []
    for raw_target in _LINK_RE.findall(content):
        target_text = raw_target.split("#", 1)[0]
        if "://" in target_text:
            continue
        target = (adr.parent / target_text).resolve()
        if not _target_is_within_root(target, root):
            findings.append(
                _finding(
                    adr,
                    root,
                    "contract-adr-link-outside-root",
                    f"Markdown link leaves the validated root: {raw_target}",
                )
            )
        elif not target.is_file():
            findings.append(
                _finding(
                    adr,
                    root,
                    "contract-adr-link-missing",
                    f"Markdown link does not resolve: {raw_target}",
                )
            )
    return findings


def _check_adr(adr: Path, root: Path) -> list[Finding]:
    content, findings = _read(adr, root)
    if content is None:
        return findings
    metadata, body, duplicate_metadata = _metadata(content)
    visible = mask_invisible_markdown(body)
    titles = [line for line in visible.splitlines() if line.startswith("# ")]
    if not titles:
        findings.append(
            _finding(
                adr,
                root,
                "contract-adr-missing-title",
                "ADR needs one level-one title",
            )
        )
    elif len(titles) > 1:
        findings.append(
            _finding(
                adr,
                root,
                "contract-adr-multiple-titles",
                "ADR needs exactly one visible level-one title",
            )
        )
    if duplicate_metadata:
        findings.append(
            _finding(
                adr,
                root,
                "contract-adr-duplicate-metadata",
                "ADR repeats metadata fields: " + ", ".join(sorted(duplicate_metadata)),
            )
        )
    status = metadata.get("status", "").casefold()
    if not status:
        findings.append(
            _finding(
                adr,
                root,
                "contract-adr-missing-status",
                "ADR needs Status metadata",
            )
        )
    elif status not in ADR_STATUSES:
        findings.append(
            _finding(
                adr,
                root,
                "contract-adr-invalid-status",
                f"ADR status '{metadata['status']}' is not one of "
                f"{', '.join(sorted(ADR_STATUSES))}",
            )
        )
    date_value = metadata.get("date")
    if not date_value:
        findings.append(_finding(adr, root, "contract-adr-missing-date", "ADR needs Date metadata"))
    else:
        try:
            parsed_date = date.fromisoformat(date_value)
        except ValueError:
            parsed_date = None
        if parsed_date is None or parsed_date.isoformat() != date_value:
            findings.append(
                _finding(
                    adr,
                    root,
                    "contract-adr-invalid-date",
                    "ADR Date metadata must be an ISO calendar date (YYYY-MM-DD)",
                )
            )
    findings.extend(_check_supersession(adr, root, metadata))
    findings.extend(_check_adr_links(adr, root, visible))
    return findings


def _check_index(directory: Path, adrs: list[Path], root: Path) -> list[Finding]:
    candidates = (directory / "README.md", directory / "index.md")
    index = next((path for path in candidates if path.is_file()), None)
    if index is None:
        return []
    content, findings = _read(index, root)
    if content is None:
        return findings
    linked = {
        (index.parent / target.split("#", 1)[0]).resolve()
        for target in _LINK_RE.findall(content)
        if "://" not in target
    }
    return findings + [
        _finding(
            index,
            root,
            "contract-adr-index-missing-entry",
            f"ADR index does not link to {adr.name}",
        )
        for adr in adrs
        if adr.resolve() not in linked
    ]


def analyze(
    root: Path,
    *,
    require_spec: bool = False,
    require_adrs: bool = False,
) -> AnalysisResult:
    """Return deterministic discovery data and validation findings for ``root``."""
    root = root.resolve()
    layout = discover(root)
    specs = list(layout.specs)
    directories = [tree.path for tree in layout.adr_trees]
    findings: list[Finding] = []
    for spec in specs:
        findings.extend(_check_spec(spec, root))
    if not specs and require_spec:
        findings.append(
            _finding(root, root, "contract-spec-required", "SPEC.md is required but was not found")
        )
    if require_adrs and not any(_adr_files(directory) for directory in directories):
        findings.append(
            _finding(
                root,
                root,
                "contract-adrs-required",
                "At least one ADR record is required but was not found",
            )
        )
    adr_count = 0
    for directory in directories:
        adrs = _adr_files(directory)
        adr_count += len(adrs)
        for adr in adrs:
            findings.extend(_check_adr(adr, root))
        findings.extend(_check_index(directory, adrs, root))
    return AnalysisResult(
        target=str(root),
        data={
            "spec": "SPEC.md" if (root / "SPEC.md") in specs else None,
            "specs": [spec.relative_to(root).as_posix() for spec in specs],
            "adr_directories": [
                directory.relative_to(root).as_posix() for directory in directories
            ],
            "adr_count": adr_count,
            "requirements": {"spec": require_spec, "adrs": require_adrs},
        },
        findings=sorted(findings),
    )
