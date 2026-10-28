"""Behavioral proof of the offline ledger; synthetic data is never model evidence."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pr_replay", ROOT / "evals/pr-writing/replay.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def fixture(tmp_path):
    root = tmp_path / "run"
    replay.plan(ROOT / "evals/pr-writing/example-manifest.json", root)
    return root, replay.read(root / "plan.json")


def receipt(tmp_path, root, trial, status="completed"):
    body = b"## Why\n\nSynthetic preview.\n\n## What changed\n\nNo write on rejection.\n\n## Risk\n\nRisk: Unassessed. No risk assessment was supplied.\n\n## Evidence\n\nSynthetic fixture only.\n"
    (tmp_path / "body.md").write_bytes(body)
    check = {"status": "no_findings", "source": {"sha256": replay.digest(body), "text": body.decode()}, "synthetic": True}
    (tmp_path / "check.json").write_text(json.dumps(check))
    r = {"plan_sha256": replay.digest((root / "plan.json").read_bytes()), "trial_id": trial, "command": ["synthetic-no-execution"], "status": status, "wall_seconds": 2 if status == "completed" else None, "timing_boundary": replay.read(root / "plan.json")["manifest"]["timing_boundary"], "phase_seconds": {}, "usage": None}
    if status == "completed":
        r.update(output_file="body.md", check_file="check.json")
    else:
        r["failure_reason"] = "synthetic interruption; terminal duration unknown"
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(r))
    return path


def test_schedule_repeats_reverse_first_arm_and_source_mismatch_fails(tmp_path):
    root, plan = fixture(tmp_path)
    s = plan["schedule"]
    assert [t["arm"] for t in s[:2]] == [t["arm"] for t in s[2:]][::-1]
    plan["inputs"][0]["sha256"] = "bad"
    with pytest.raises(ValueError, match="Frozen input"):
        replay.inputs_unchanged(plan)


def test_failure_unknown_is_retained_and_cannot_be_replaced(tmp_path):
    root, plan = fixture(tmp_path)
    r = receipt(tmp_path, root, plan["schedule"][0]["id"], "interrupted")
    replay.record(root, r)
    with pytest.raises(ValueError, match="already retained"):
        replay.record(root, r)
    summary = replay.summary(root)
    assert summary["completed"] == 0 and len(summary["failures"]) == 1
    assert summary["pairs"][0]["percent_change"] is None
    assert summary["unknown_usage_attempts"] == 1


def test_stale_final_check_is_rejected(tmp_path):
    root, plan = fixture(tmp_path)
    r = receipt(tmp_path, root, plan["schedule"][0]["id"])
    (tmp_path / "body.md").write_text("Changed after check")
    with pytest.raises(ValueError, match="Stale final check"):
        replay.record(root, r)


def test_blind_exact_bytes_and_locked_dataset_bound_join(tmp_path):
    root, plan = fixture(tmp_path)
    for trial in plan["schedule"]:
        replay.record(root, receipt(tmp_path, root, trial["id"]))
    blind = tmp_path / "blind"
    replay.blind(root, blind, 21)
    public = replay.read(blind / "public/pairs.json")
    key = replay.read(blind / "private/key.json")
    assert len(public["cases"]) == 2
    assert {c["sides"]["A"]["arm"] for c in key["cases"]} == {"original", "candidate"}
    for row, hidden in zip(public["cases"], key["cases"]):
        for side in ["A", "B"]:
            assert replay.digest(row[side.lower() + "_markdown"].encode()) == hidden["sides"][side]["output_sha256"]
    labels = tmp_path / "labels.json"
    labels.write_text(json.dumps({"locked": True, "pairs_sha256": key["pairs_sha256"], "labels": [{"case_id": "pair-001", "choice": "tie", "notes": "same synthetic text"}]}))
    assert replay.join(blind / "private/key.json", labels)[0]["preferred_arm"] == "tie"
    d = replay.read(labels); d["pairs_sha256"] = "wrong"; labels.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="different blind payload"):
        replay.join(blind / "private/key.json", labels)


def test_source_drift_failure_retains_known_cost(tmp_path):
    root, plan = fixture(tmp_path)
    r = receipt(tmp_path, root, plan["schedule"][0]["id"], "failed")
    plan["inputs"][0]["sha256"] = "changed"
    (root / "plan.json").write_text(json.dumps(plan))
    data = replay.read(r)
    data["plan_sha256"] = replay.digest((root / "plan.json").read_bytes())
    data["usage"] = {"input_tokens": 123, "cached_input_tokens": 100}
    r.write_text(json.dumps(data))
    replay.record(root, r)
    saved = replay.read(root / "receipts" / (data["trial_id"] + ".json"))
    assert saved["input_integrity"] == "changed_or_unavailable"
    assert saved["usage"]["input_tokens"] == 123


def test_inline_fields_cannot_bypass_byte_digest_binding(tmp_path):
    root, plan = fixture(tmp_path)
    path = receipt(tmp_path, root, plan["schedule"][0]["id"])
    data = replay.read(path)
    data.pop("output_file")
    data.update(output_text="Actual final text", output_sha256="wrong-digest")
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="requires an output file"):
        replay.record(root, path)
