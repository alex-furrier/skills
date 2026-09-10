# Reproducible validation

Run the complete release check from the catalog root after verifying `uv --version` and `vale --version`:

```bash
python scripts/fast_check.py
```

It validates provenance and copied artifacts, type checks the Context CLI and repository automation, runs behavioral tests, builds MkDocs strictly, runs a Context reference check, runs advisory Writing Check evidence, and finishes with `git diff --check`.

Run Mypy directly with:

```bash
uv run --no-config --locked --project plugins/context-engineering/cli mypy --config-file mypy.ini \
  plugins/context-engineering/cli/src/context_engineering scripts \
  plugins/context-engineering/skills/context-docs/scripts \
  skills/writing/writing-check/scripts skills/writing/pr-description/scripts tests
```

For an isolated Context check, use the complete plugin:

```bash
uv run --no-config --locked --no-dev --project plugins/context-engineering/cli \
  context-engineering check . --json
```

For an isolated Writing Check, use the self-contained skill:

```bash
uv run --python 3.11 python \
  skills/writing/writing-check/scripts/writing_check.py \
  --profile technical-doc --json README.md
```

Vale is required for the release check; `unavailable` is incomplete prerequisite evidence. Writing findings remain advisory, so a findings exit is accepted. Do not validate Context from a selected-skill copy: only the plugin installation carries its CLI.

## Local Context workflow benchmark

This is advisory local evidence, not a CI time gate. On a clean worktree, warm the
locked environment once, then run five to ten samples of the former two-command
workflow and the composed workflow. Discard the first sample and report median
and p95 separately; retain JSON and compare exit status plus `changed_paths`,
`evidence`, and `advisory_routes`, not only elapsed time.

```bash
# Former workflow: two processes and duplicate diff analysis.
uv run --no-config --locked --no-dev --project plugins/context-engineering/cli context-engineering check . --base HEAD^ --head HEAD --json >/dev/null
uv run --no-config --locked --no-dev --project plugins/context-engineering/cli context-engineering review . --base HEAD^ --head HEAD --json >/dev/null

# Current workflow: check already retains review evidence.
uv run --no-config --locked --no-dev --project plugins/context-engineering/cli context-engineering check . --base HEAD^ --head HEAD --json >/dev/null
```

On this macOS worktree at `465967a`, pre-change warm samples were 2.16–3.25 s
for `check` plus 1.74–2.84 s for `review`. After consolidating the documented
workflow, warm `check` samples were 2.68 s and 3.32 s (about 3.00 s median,
two samples); initial locked-environment provisioning was measured separately
at 4.17 s and is not included in the warm result. The reduction removes one
`uv`/Python process and its repeated Git diff work; it does not change Context
analysis or impose a timing assertion.

## Local Writing Check sweep benchmark

This is advisory local evidence, not a CI gate. After the repository workflow
has explicitly selected candidates, write their exact source/profile pairs to
`pairs.json`. Compare five to ten warm samples (discard the first; report median
and p95) of one checker process per pair with the bounded caller below. Retain
and compare every schema-v3 record and status, not just elapsed time.

```bash
# Baseline: one checker process and Vale version probe per explicit pair.
python3 -c '
import json, subprocess, sys
for pair in json.load(open(sys.argv[1], encoding="utf-8")):
    subprocess.run([
        "python3", "skills/writing/writing-check/scripts/writing_check.py",
        "--profile", pair["profile"], "--json", "--", pair["source"],
    ], check=False)
' pairs.json >/dev/null

# Consolidated: one Python startup and one shared Vale version probe.
python3 skills/writing/writing-check/scripts/repository_sweep_check.py \
  --candidates pairs.json --jsonl >/dev/null
```

For N candidates, consolidation removes N-1 Python process startups and N-1
Vale version probes; lint execution, policy validation, source reads, and each
independent schema-v3 record remain per candidate. Do not set a wall-clock
threshold: behavioral tests, not timing, establish the consolidation.
