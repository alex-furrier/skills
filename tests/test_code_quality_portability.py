"""The release guard rejects removed plumbing in copied portable artifacts."""
import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize("token", [
    "Dots", "Pi subagents", "codemode", "ai-runtime", "ai_runtime",
    "Groundskeeper", "Harness Kit", "~/.agent", "alex-ai-experimental",
    "/Users/example/tools", "/home/example/tools",
])
def test_removed_plumbing_is_rejected_in_suite_and_package(tmp_path, token):
    spec = importlib.util.spec_from_file_location("fast_check", Path(__file__).parents[1] / "scripts/fast_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    for directory in ("skills/code-quality", "packages/code-health"):
        path = tmp_path / directory / "example.md"
        path.parent.mkdir(parents=True)
        path.write_text("Review the owning module inline.\n")
        module.check_code_quality_portability()
        path.write_text(token)
        with pytest.raises(SystemExit, match="removed execution plumbing"):
            module.check_code_quality_portability()
        path.unlink()
