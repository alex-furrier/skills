#!/usr/bin/env python3
"""Validate the public, frozen Batch 0 evaluation manifest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
MANIFEST = EVALS / "manifest.json"
EVIDENCE_KINDS = {
    "deterministic",
    "model-forward-development",
    "held-out-adoption",
}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "catalog_revision",
    "cases",
}
CASE_FIELDS = {
    "id",
    "evidence_kind",
    "prompt",
    "fixture",
    "applicable_skills",
    "must_observe",
    "must_not",
    "protected_exact_text",
}


def skill_names() -> set[str]:
    """Return the public skill directory names without parsing skill prose."""
    roots = (ROOT / "plugins/context-engineering/skills", ROOT / "skills/writing")
    return {path.parent.name for root in roots for path in root.glob("*/SKILL.md")}


def nonempty_strings(value: Any, field: str, case_id: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        errors.append(f"{case_id}: {field} must be a non-empty list of strings")
        return []
    return value


def validate_case(case: Any, known_skills: set[str], seen_ids: set[str], errors: list[str]) -> None:
    if not isinstance(case, dict):
        errors.append("case must be an object")
        return
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        errors.append("case id must be a non-empty string")
        return
    if case_id in seen_ids:
        errors.append(f"duplicate case id: {case_id}")
    seen_ids.add(case_id)
    fields = set(case)
    missing = CASE_FIELDS - fields
    unknown = fields - CASE_FIELDS
    if missing:
        errors.append(f"{case_id}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{case_id}: unknown fields: {', '.join(sorted(unknown))}")
    for field in ("prompt", "fixture", "evidence_kind"):
        if not isinstance(case.get(field), str) or not case[field]:
            errors.append(f"{case_id}: {field} must be a non-empty string")
    if case.get("evidence_kind") not in EVIDENCE_KINDS:
        errors.append(f"{case_id}: unknown evidence_kind")
    skills = nonempty_strings(case.get("applicable_skills"), "applicable_skills", case_id, errors)
    unknown_skills = set(skills) - known_skills
    if unknown_skills:
        errors.append(f"{case_id}: unknown skills: {', '.join(sorted(unknown_skills))}")
    for field in ("must_observe", "must_not"):
        nonempty_strings(case.get(field), field, case_id, errors)
    protected = case.get("protected_exact_text")
    if not isinstance(protected, list) or not all(isinstance(item, str) and item for item in protected):
        errors.append(f"{case_id}: protected_exact_text must be a list of non-empty strings; an empty list is allowed")
    fixture = case.get("fixture")
    if isinstance(fixture, str) and fixture:
        path = (EVALS / fixture).resolve()
        if EVALS not in path.parents or not path.is_file():
            errors.append(f"{case_id}: fixture does not exist under evals: {fixture}")
        elif isinstance(protected, list):
            text = path.read_text(encoding="utf-8")
            for protected_text in protected:
                if isinstance(protected_text, str) and protected_text not in text:
                    errors.append(f"{case_id}: protected text is absent from fixture")


def validate_manifest(manifest: Path = MANIFEST) -> list[str]:
    """Return schema and fixture-reference errors without invoking model tooling."""
    errors: list[str] = []
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid eval manifest: {error}"]
    if not isinstance(data, dict):
        return ["eval manifest must be an object"]
    fields = set(data)
    missing = TOP_LEVEL_FIELDS - fields
    unknown = fields - TOP_LEVEL_FIELDS
    if missing:
        errors.append(f"eval manifest missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"eval manifest unknown fields: {', '.join(sorted(unknown))}")
    if data.get("schema_version") != 1:
        errors.append("eval manifest schema_version must be 1")
    if not isinstance(data.get("catalog_revision"), str) or not data["catalog_revision"]:
        errors.append("eval manifest must name a catalog_revision")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["eval manifest must contain cases"]
    seen_ids: set[str] = set()
    known_skills = skill_names()
    for case in cases:
        validate_case(case, known_skills, seen_ids, errors)
    return errors


def main() -> int:
    errors = validate_manifest()
    print("\n".join(errors) if errors else "eval manifest validation passed")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
