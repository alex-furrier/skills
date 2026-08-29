"""Classify changed files by impact (HIGH / MEDIUM / LOW).

The patterns live here — staleness.py just calls classify() so there's one
place to add a new high-impact filename.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Impact(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ImpactClassification:
    impact: Impact
    reason: str


def _rule(pattern: str, reason: str) -> tuple[re.Pattern[str], str]:
    return re.compile(pattern), reason


_HIGH = (
    _rule(r"(^|/)package\.json$", "dependency manifest"),
    _rule(r"(^|/)pyproject\.toml$", "Python project manifest"),
    _rule(r"(^|/)Cargo\.toml$", "Rust project manifest"),
    _rule(r"(^|/)go\.(mod|sum)$", "Go dependency manifest"),
    _rule(r"(^|/)pom\.xml$", "Maven project manifest"),
    _rule(r"(^|/)build\.gradle", "Gradle build configuration"),
    _rule(r"(^|/)Makefile$", "Make build entrypoint"),
    _rule(r"(^|/)Taskfile", "Task runner configuration"),
    _rule(r"(^|/)justfile$", "Just task runner configuration"),
    _rule(r"(^|/)\.mise\.toml$", "mise task and tool configuration"),
    _rule(r"(^|/)\.github/workflows/", "GitHub Actions workflow"),
    _rule(r"(^|/)\.gitlab-ci", "GitLab CI configuration"),
    _rule(r"(^|/)Jenkinsfile", "Jenkins pipeline"),
    _rule(r"(^|/)Dockerfile", "container build definition"),
    _rule(r"(^|/)docker-compose", "container composition configuration"),
    _rule(r"(^|/)\.pre-commit-config\.yaml$", "pre-commit configuration"),
)

_MEDIUM = (
    _rule(r"(^|/)README", "README documentation"),
    _rule(r"(^|/)CHANGELOG", "changelog"),
    _rule(r"(^|/)setup\.(py|cfg)$", "Python package configuration"),
    _rule(r"(^|/)requirements.*\.txt$", "Python dependency list"),
)


def classify_with_reason(filepath: str) -> ImpactClassification:
    for pattern, reason in _HIGH:
        if pattern.search(filepath):
            return ImpactClassification(Impact.HIGH, f"matched high-impact rule: {reason}")
    for pattern, reason in _MEDIUM:
        if pattern.search(filepath):
            return ImpactClassification(Impact.MEDIUM, f"matched medium-impact rule: {reason}")
    # Shallow paths (top-level changes) default to MEDIUM; deep paths are LOW
    if len(filepath.split("/")) <= 2:
        return ImpactClassification(
            Impact.MEDIUM,
            "no named rule matched; paths at depth 2 or less default to medium impact",
        )
    return ImpactClassification(
        Impact.LOW,
        "no named rule matched; paths deeper than 2 components default to low impact",
    )


def classify(filepath: str) -> Impact:
    return classify_with_reason(filepath).impact
