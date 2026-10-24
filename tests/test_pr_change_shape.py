"""Keep requirements documentation distinct from executable test changes."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pr_change_shape", ROOT / "skills/writing/pr-description/scripts/pr_change_shape.py"
)
assert SPEC and SPEC.loader
shape = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shape)


@pytest.mark.parametrize("path", ["SPEC.md", "docs/SPEC.md", "spec.md", "specs/SPEC.md"])
def test_markdown_spec_is_documentation(path: str) -> None:
    result = shape.classify_file(path.encode(), {})
    assert result["bucket"] == "supporting"
    assert result["supporting_kind"] == "docs"


@pytest.mark.parametrize("path", ["src/widget.spec.ts", "tests/test_widget.py", "spec/widget.rb"])
def test_executable_specs_and_tests_still_have_test_role(path: str) -> None:
    result = shape.classify_file(path.encode(), {})
    assert result["bucket"] == "supporting"
    assert result["supporting_kind"] == "test"


def test_explicit_attributes_keep_precedence() -> None:
    generated = shape.classify_file(b"SPEC.md", {"linguist-generated": "true"})
    assert generated["supporting_kind"] == "generated"
    explicitly_not_docs = shape.classify_file(b"SPEC.md", {"linguist-documentation": "false"})
    assert explicitly_not_docs["bucket"] == "core"
