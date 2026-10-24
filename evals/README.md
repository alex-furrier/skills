# Batch 0 evaluations

`manifest.json` is versioned, machine-readable baseline evidence. It records fixed prompts, public fixtures, applicable skills, required and prohibited observable behavior, and protected exact text. It is not a prose scorecard or an automatic semantic judge.

## Validate the surface

Run this deterministic check from the catalog root:

```bash
python scripts/validate_evals.py
```

The check validates schema fields, fixture references, public skill names, and protected text that a fixture supplies. It does not run a model or grade an answer.

## Run development evidence

A coordinator selects a small fixed set of `model-forward-development` cases and gives each prompt and fixture to a fresh isolated agent. The coordinator records the selected skills and profiles, commands proposed or invoked, mutation decision, protected text, source-bound checker status where applicable, and the unedited output. Freeze that output with the manifest revision before grading it against `must_observe` and `must_not`.

Use the same baseline cases and fixture revision for candidate comparisons. Keep baseline and candidate development evidence separate from `held-out-adoption` evidence. Held-out adoption uses consented, de-identified real requests that were not used to change the skills; do not add those requests or outputs to this public catalog by default.

Reviewers make the semantic judgment. Mission, reviewer, or checker status is evidence only; none is acceptance. In particular, an `unavailable` Writing Check result is missing evidence, and checker findings never authorize edits or establish readiness. This repository intentionally provides no model launcher, credentials, scoring framework, or automatic semantic judge.

## Paired PR-writing process trials

[pr-writing/README.md](pr-writing/README.md) adds an optional offline receipt ledger for an existing native harness: frozen schedules/inputs, retained failures, actual telemetry, exact blind pairs and locked preference joining. No model launcher or automatic quality judge. Only synthetic fixtures and sanitized aggregate evidence are shipped.
