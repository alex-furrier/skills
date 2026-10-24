# Repeatable paired PR-writing trials

This standard-library tool supports an existing native agent harness: frozen inputs/settings, seeded alternating schedule, append-only failure receipts, exact-byte blind pairs and locked preference joining. It does **not** launch a model, acquire credentials, infer token counts, run a reviewer or grade prose. It is not the private native recorder used in the historical study. The synthetic example proves receipt plumbing, not writing performance.

## Freeze and execute locally

```sh
python3 evals/pr-writing/replay.py plan evals/pr-writing/example-manifest.json /tmp/pr-trials
cat /tmp/pr-trials/plan.json
```

For real trials, keep a manifest and inputs in a private ignored directory outside the repository. Replace synthetic settings, pin source snapshots/prompts/skill dependencies by SHA-256 under `inputs`, and predeclare exact model/reasoning, cache conditions, task, arm definitions, quality gates, timing boundary, repeats and budget. Cases should record immutable base/head, source provenance, diff size and omitted/generated/binary material. Give both arms equivalent source/rationale/validation access. Preserve contradictions. Keep development separate from unseen outputs; observed cases are no longer holdouts after tuning.

Execute schedule entries sequentially through the **same supported native harness**, identical model/reasoning and drafting/check/repair policy. Even repeats reverse each pair's first arm. Avoid concurrent writers, heavy background work and grading while timing. Record UTC/monotonic clocks, load timestamps, tool/runtime versions, native commands, actual token/cache counters and private raw evidence. Unknown server settings, queue/inference timing or usage remain unknown. Fresh historical replay is not a genuine warm implementation continuation.

Time from before per-run acquisition/verification through delivered final bytes, checks, necessary repairs and final source verification. Include candidate preparation/retries. Keep shared remote acquisition, setup, review and evaluation overhead separately visible. Phase intervals may overlap or nest; do not sum them as a critical path. The ledger imports measurements, and cannot independently attest supplied durations, telemetry, commands or check execution.

Write one local receipt per actual attempt:

```json
{
  "plan_sha256": "SHA256 OF THE ACTUAL plan.json BYTES",
  "trial_id": "synthetic-cli-r1-original",
  "status": "completed",
  "command": ["your-existing-harness", "actual-arguments"],
  "timing_boundary": "COPY THE FROZEN timing_boundary EXACTLY",
  "wall_seconds": 42.5,
  "phase_seconds": {"collection": 1.2, "writer_and_checks": 41.3},
  "usage": {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20},
  "output_file": "body.md",
  "check_file": "writing-check.json"
}
```

These numbers illustrate schema, **not observed evidence**. File paths resolve relative to the receipt. Use actual native usage only; `null` means unavailable. Cached input is a subset of input; reasoning a subset of output. Do not double count them, estimate tokens from bytes or infer money from subscription counters. Keep raw events, prompts, checks, tool-roundtrip and load/clock records privately; optional extra receipt fields retain references. For `failed`/`interrupted`, retain `failure_reason`, exposed partial usage and known duration. Unknown terminal time is `null`, not zero. A missing draft is neither a quality failure nor a successful fast outcome.

```sh
python3 evals/pr-writing/replay.py record /tmp/pr-trials /path/to/private/receipt.json
python3 evals/pr-writing/replay.py summary /tmp/pr-trials
```

Record rechecks input digests, rejects duplicate attempts and binds final output to retained checker text/SHA. It embeds exact output/check bytes so later file edits cannot change the saved receipt. An unusable check cannot mark completion. Retries or changed sources/methods need a separately authorized new plan; never overwrite a failure or substitute a favorable case. This is not a tamper-proof archive or execution attestation. No automatic retry, schedule execution or resume occurs.

Summary retains every pair, unknown/failure counts, matched per-case medians and actual token totals with unknown counts. Tokens include all recorded attempts per arm, while paired effects require two completed outputs; compare matched token subsets separately when counts differ. Inspect case distributions and correlated repeats, not only pooled medians. Assess factual quality separately from prose preference; latency is not adoption.

## Blind review and joining

```sh
python3 evals/pr-writing/replay.py blind /tmp/pr-trials /tmp/pr-blind --seed 73
```

Show only `/tmp/pr-blind/public/pairs.json`. Keep `private/key.json`, methods, timing, receipts and judgments private until explicit lock/reveal. Sides are balanced within one slot, independently randomized from execution order and persisted once; do not reshuffle on reload. Export includes complete pairs only: disclose exclusions using summary. Inspect exact texts for private content or method self-identification and flag contamination privately; do not silently edit output. This tool does not sanitize content or authorize publication. Give factual assessors neutral original source/context separately, without answers or methods.

Independent assessors check factual grounding, important behavior/intent, honest validation, compatibility/failure/auth/ownership boundaries, contradictions, inspectable witnesses/limits and required format/inventories. Material failures need exact source evidence and reader consequence; preserve precision notes, uncertainty and disagreement. Keep gold outside writer prompts. Passing lint is not semantic quality; graders do not veto what a human may inspect.

After explicit lock, join a label file:

```json
{
  "locked": true,
  "pairs_sha256": "SHA256 OF EXACT public/pairs.json BYTES",
  "labels": [{"case_id": "pair-001", "choice": "tie", "notes": "Similar usefulness"}]
}
```

```sh
python3 evals/pr-writing/replay.py join /tmp/pr-blind/private/key.json /path/to/locked-labels.json
```

Choices are A/B/tie/neither. Join rejects duplicate/unknown labels and mismatched payload identity. Lock is declarative; the tool cannot prevent early key access. Check side preference as well as method. Two assessors sharing an orientation do not independently rule out position bias. Preserve existing viewer votes and assignments; never publish private labels/keys without authorization.

## Offline proof and provenance

```sh
python3 -m pytest -q tests/test_pr_writing_replay.py tests/test_pr_change_shape.py
```

Tests cover synthetic alternating repeats, unknown interrupted cost, duplicate rejection, changed input/stale check rejection, exact blind bytes, balanced sides and locked dataset-bound joining. No model/network/private history. Utility and fixture are independently authored under the catalog MIT license; no private session script, trace, source diff or third-party code was copied. The helper is separate from Batch0's existing manifest/schema.

See [study-summary.md](study-summary.md) for sanitized aggregate evidence and limits. Supply private inputs locally; commit no outputs, traces or labels by default.
