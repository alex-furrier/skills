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
