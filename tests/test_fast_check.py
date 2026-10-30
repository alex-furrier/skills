"""Verifier boundary tests; packaged CLI tests exercise the actual Vale runtime."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


@pytest.fixture
def verifier(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("fast_check", Path(__file__).parents[1] / "scripts/fast_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    text = "Open the settings panel!\n"
    (tmp_path / "README.md").write_text(text)
    record = {
        "schema": 3, "profile": "readme", "advisory": True, "status": "findings",
        "source": {"kind": "file", "identifier": str(tmp_path / "README.md"),
                   "text": text, "bytes": len(text.encode()), "sha256": hashlib.sha256(text.encode()).hexdigest()},
        "alerts": [{"rule": "GoogleDocs.Exclamation"}], "vale": {"status": "ran"},
    }
    binaries = tmp_path / "bin"
    binaries.mkdir()
    monkeypatch.setenv("PATH", f"{binaries}{os.pathsep}{os.environ.get('PATH', '')}")

    def command(body):
        uv = binaries / "uv"
        uv.write_text(f"#!{sys.executable}\n{body}\n")
        uv.chmod(0o755)

    return module, record, command


@pytest.mark.parametrize("status,code", [("findings", 1), ("no_findings", 0)])
def test_readme_verifier_accepts_usable_advisory_results(verifier, status, code):
    module, record, command = verifier
    record["status"] = status
    record["alerts"] = record["alerts"] if code else []
    command(f"print({json.dumps(record)!r})\nraise SystemExit({code})")
    module.run_readme_check()


@pytest.mark.parametrize("body", [
    "raise ModuleNotFoundError(\"No module named 'writing_check'\")",
    "raise SystemExit(1)",
], ids=["import-crash", "empty-stdout"])
def test_readme_verifier_rejects_exit_one_without_evidence(verifier, body):
    module, _, command = verifier
    command(body)
    with pytest.raises(SystemExit, match="README Writing Check evidence failed validation"):
        module.run_readme_check()


@pytest.mark.parametrize("fault", [
    "malformed", "stale-sha", "wrong-source", "error-status",
    "status-exit-mismatch", "empty-findings", "vale-not-ran",
])
def test_readme_verifier_rejects_unusable_or_misbound_records(verifier, fault):
    module, template, command = verifier
    record = copy.deepcopy(template)
    if fault == "stale-sha":
        record["source"]["sha256"] = "0" * 64
    elif fault == "wrong-source":
        record["source"]["identifier"] = "/another/README.md"
    elif fault == "error-status":
        record["status"] = "execution_error"
    elif fault == "status-exit-mismatch":
        record["status"], record["alerts"] = "no_findings", []
    elif fault == "empty-findings":
        record["alerts"] = []
    elif fault == "vale-not-ran":
        record["vale"]["status"] = "unavailable"
    payload = "{" if fault == "malformed" else json.dumps(record)
    command(f"print({payload!r})\nraise SystemExit(1)")
    with pytest.raises(SystemExit, match="README Writing Check evidence failed validation"):
        module.run_readme_check()
