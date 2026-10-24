#!/usr/bin/env python3
"""Offline, append-only paired-trial receipts. Does not launch models or judge prose."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def inputs_unchanged(plan: dict[str, Any]) -> None:
    for item in plan["inputs"]:
        require(digest(Path(item["path"]).read_bytes()) == item["sha256"], "Frozen input changed")


def plan(manifest: Path, out: Path) -> None:
    raw = manifest.read_bytes()
    m = json.loads(raw)
    require(m["schema_version"] == 1, "Unsupported schema")
    require(set(m["arms"]) == {"original", "candidate"}, "Expected original/candidate arms")
    require(isinstance(m["repeats"], int) and m["repeats"] > 0, "Positive repeat count required")
    require(all(m.get(k) for k in ["model", "reasoning", "timing_boundary", "quality_gates", "cases", "inputs"]), "Missing fixed conditions")
    ids = [c["id"] for c in m["cases"]]
    require(len(set(ids)) == len(ids), "Duplicate case")
    require(all(isinstance(i, str) and i.isascii() and i.replace("-", "").isalnum() for i in ids), "Case IDs must be ASCII letters/digits/hyphens")
    pinned = []
    for item in m["inputs"]:
        path = (manifest.parent / item["path"]).resolve()
        require(digest(path.read_bytes()) == item["sha256"], "Input digest mismatch")
        pinned.append({"path": str(path), "sha256": item["sha256"]})
    rng = random.Random(m["seed"])
    cases = list(ids)
    rng.shuffle(cases)
    schedule = []
    for case in cases:
        first = rng.choice(["original", "candidate"])
        for repeat in range(1, m["repeats"] + 1):
            order = [first, "candidate" if first == "original" else "original"]
            if repeat % 2 == 0:
                order.reverse()
            for arm in order:
                schedule.append({"id": f"{case}-r{repeat}-{arm}", "case": case, "repeat": repeat, "arm": arm})
    frozen = {"manifest_sha256": digest(raw), "manifest": m, "inputs": pinned, "schedule": schedule}
    out.mkdir(mode=0o700, exist_ok=False)
    (out / "receipts").mkdir()
    write(out / "plan.json", frozen)


def record(root: Path, receipt: Path) -> None:
    frozen = read(root / "plan.json")
    r = read(receipt)
    try:
        inputs_unchanged(frozen)
        r["input_integrity"] = "unchanged"
    except (ValueError, OSError):
        require(r.get("status") in {"failed", "interrupted"}, "Frozen input changed; retain attempt as failed/interrupted")
        r["input_integrity"] = "changed_or_unavailable"
    require(r["plan_sha256"] == digest((root / "plan.json").read_bytes()), "Wrong plan identity")
    require(r["trial_id"] in {t["id"] for t in frozen["schedule"]}, "Unknown trial")
    target = root / "receipts" / (r["trial_id"] + ".json")
    require(not target.exists(), "Attempt already retained; use a new separately authorized plan for retries")
    require(r["status"] in {"completed", "failed", "interrupted"}, "Unknown status")
    require(r.get("wall_seconds") is None or number(r["wall_seconds"]), "Invalid wall time")
    require(r["status"] != "completed" or number(r.get("wall_seconds")), "Completed outcome needs actual duration")
    require(isinstance(r.get("command"), list) and r["command"] and all(isinstance(s, str) for s in r["command"]), "Record exact executed command")
    require(r.get("timing_boundary") == frozen["manifest"]["timing_boundary"], "Unmatched timing boundary")
    require(r.get("failure_reason") or r["status"] == "completed", "Retain failure reason/unknown cause")
    require(all(number(v) for v in r.get("phase_seconds", {}).values()), "Invalid phase duration")
    usage = r.get("usage")
    require(usage is None or isinstance(usage, dict), "Usage must be telemetry or null")
    if usage is not None:
        require(all(v is None or (number(v) and isinstance(v, int)) for v in usage.values()), "Invalid token count")
        for subset, total in [("cached_input_tokens", "input_tokens"), ("reasoning_output_tokens", "output_tokens")]:
            require(usage.get(subset) is None or usage.get(total) is None or usage[subset] <= usage[total], "Token subset exceeds total")
    require(r["status"] != "completed" or r.get("output_file"), "Completed outcome requires an output file")
    # Read exact bytes into the receipt; do not depend on mutable output files later.
    if r.get("output_file"):
        body = (receipt.parent / r.pop("output_file")).read_bytes()
        r["output_sha256"] = digest(body)
        r["output_text"] = body.decode("utf-8")
    if r["status"] == "completed":
        require("output_text" in r and "check_file" in r, "Completed outcome needs final output and bound check")
        check = read(receipt.parent / r.pop("check_file"))
        require(check["source"]["sha256"] == r["output_sha256"] and check["source"]["text"] == r["output_text"], "Stale final check")
        require(check["status"] in {"no_findings", "findings"}, "Unusable final check")
        r["final_check"] = check
    r["receipt_input_sha256"] = digest(receipt.read_bytes())
    write(target, r)


def summary(root: Path) -> dict[str, Any]:
    p = read(root / "plan.json")
    records = {t["id"]: read(root / "receipts" / (t["id"] + ".json")) for t in p["schedule"] if (root / "receipts" / (t["id"] + ".json")).exists()}
    pairs = []
    for c in p["manifest"]["cases"]:
        for repeat in range(1, p["manifest"]["repeats"] + 1):
            rr = {a: records.get(f"{c['id']}-r{repeat}-{a}") for a in ["original", "candidate"]}
            complete = all(v and v["status"] == "completed" for v in rr.values())
            pairs.append({"case": c["id"], "repeat": repeat, "complete": complete, "seconds": {a: v.get("wall_seconds") if v else None for a, v in rr.items()}, "percent_change": (rr["candidate"]["wall_seconds"] / rr["original"]["wall_seconds"] - 1) * 100 if complete and rr["original"]["wall_seconds"] else None})
    by_case = []
    for c in p["manifest"]["cases"]:
        complete = [x for x in pairs if x["case"] == c["id"] and x["complete"]]
        by_case.append({"case": c["id"], "complete_pairs": len(complete), "matched_arm_medians_seconds": {a: statistics.median(x["seconds"][a] for x in complete) if complete else None for a in ["original", "candidate"]}})
    telemetry = {}
    for arm in ["original", "candidate"]:
        rr = [records[t["id"]] for t in p["schedule"] if t["arm"] == arm and t["id"] in records]
        telemetry[arm] = {field: {"known_sum": sum(r["usage"][field] for r in rr if r.get("usage") and r["usage"].get(field) is not None), "unknown_attempts": sum(not r.get("usage") or r["usage"].get(field) is None for r in rr)} for field in ["input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"]}
    effects = [p["percent_change"] for p in pairs if p["percent_change"] is not None]
    return {"scheduled": len(p["schedule"]), "retained": len(records), "completed": sum(r["status"] == "completed" for r in records.values()), "failures": {k: r["status"] for k, r in records.items() if r["status"] != "completed"}, "unknown_usage_attempts": sum(r.get("usage") is None for r in records.values()), "pairs": pairs, "by_case": by_case, "actual_telemetry": telemetry, "median_paired_percent_change": statistics.median(effects) if effects else None, "warning": "Descriptive correlated repeats; inspect PR-level medians, all failures and independent quality separately. No automatic adoption."}


def blind(root: Path, out: Path, seed: int) -> None:
    p = read(root / "plan.json")
    candidates = [x for x in summary(root)["pairs"] if x["complete"]]
    rng = random.Random(seed)
    rng.shuffle(candidates)
    first = ["original"] * (len(candidates) // 2) + ["candidate"] * (len(candidates) - len(candidates) // 2)
    rng.shuffle(first)
    public, key = [], []
    for i, (pair, a) in enumerate(zip(candidates, first), 1):
        row: dict[str, Any] = {"case_id": f"pair-{i:03d}"}
        hidden: dict[str, Any] = {"case_id": row["case_id"], "source_case": pair["case"], "repeat": pair["repeat"], "sides": {}}
        for side, arm in [("A", a), ("B", "candidate" if a == "original" else "original")]:
            r = read(root / "receipts" / f"{pair['case']}-r{pair['repeat']}-{arm}.json")
            row[side.lower() + "_markdown"] = r["output_text"]
            hidden["sides"][side] = {"arm": arm, "output_sha256": r["output_sha256"]}
        public.append(row)
        key.append(hidden)
    out.mkdir(mode=0o700, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir(mode=0o700)
    write(out / "public/pairs.json", {"cases": public})
    write(out / "private/key.json", {"pairs_sha256": digest((out / "public/pairs.json").read_bytes()), "plan_sha256": digest((root / "plan.json").read_bytes()), "seed": seed, "cases": key})


def join(key_file: Path, labels_file: Path) -> list[dict[str, Any]]:
    key = read(key_file)
    keys = {x["case_id"]: x for x in key["cases"]}
    labels = read(labels_file)
    require(labels.get("pairs_sha256") == key["pairs_sha256"], "Labels belong to a different blind payload")
    require(labels.get("locked") is True, "Lock labels before reveal")
    seen: set[str] = set()
    rows = []
    for r in labels["labels"]:
        cid, choice = r["case_id"], r["choice"]
        require(cid in keys and cid not in seen, "Unknown or duplicate label")
        require(choice in {"A", "B", "tie", "neither"}, "Unknown preference")
        seen.add(cid)
        rows.append({**r, "preferred_arm": keys[cid]["sides"][choice]["arm"] if choice in {"A", "B"} else choice, "source_case": keys[cid]["source_case"], "repeat": keys[cid]["repeat"]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name, args in [("plan", ["manifest", "out"]), ("record", ["root", "receipt"]), ("summary", ["root"]), ("blind", ["root", "out"]), ("join", ["key", "labels"])]:
        cmd = sub.add_parser(name)
        for arg in args:
            cmd.add_argument(arg, type=Path)
        if name == "blind":
            cmd.add_argument("--seed", type=int, required=True)
    a = parser.parse_args()
    try:
        if a.action == "plan":
            plan(a.manifest, a.out)
        elif a.action == "record":
            record(a.root, a.receipt)
        elif a.action == "summary":
            print(json.dumps(summary(a.root), indent=2))
        elif a.action == "blind":
            blind(a.root, a.out, a.seed)
        else:
            print(json.dumps(join(a.key, a.labels), indent=2))
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
