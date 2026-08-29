# Reproducible validation

The release check is deliberately evidence-oriented and read-only for source content.
Run it from a clean checkout:

```bash
./scripts/fast-check.sh
```

It runs behavioral tests, validates a copied release artifact and provenance coverage, builds MkDocs with `--strict`, runs the Context reference check, runs the exact-input Writing Check against `README.md`, and finishes with `git diff --check`.

The expected Writing Check state is either `no_findings` when Vale is installed or `unavailable` when it is not. Both records retain the exact source identity; neither is a factual or publication verdict. The command does not install Vale or download styles.

For an isolated context check, use:

```bash
PYTHONPATH=packages/context-engineering uv run --python 3.11 python -m context_engineering check . --json
```

For an isolated selected-skill check, copy `skills/writing/writing-check` and run its bundled checker script. The test suite verifies that missing Vale produces the explicit `unavailable` state rather than a clean result.
