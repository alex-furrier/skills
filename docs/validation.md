# Reproducible validation

The release check is deliberately evidence-oriented and read-only for source
content. Run it from a complete catalog checkout after verifying `uv --version`
and `vale --version`:

```bash
python scripts/fast_check.py
```

It verifies the Context lock without network access, runs static type checking
with pinned Mypy and behavioral tests, validates a copied release artifact and
provenance coverage, builds MkDocs with `--strict`, runs the installed Context
reference check, runs the exact-input Writing Check against `README.md`, and
finishes with `git diff --check`. Context commands use `--no-config --locked` so
machine-level resolver policy cannot rewrite or invalidate the shipped lock.

Run the type checker directly with:

```bash
uv run --no-config --locked --project packages/context-engineering mypy --config-file mypy.ini \
  packages/context-engineering/context_engineering packages/writing-check/scripts \
  scripts skills/context/context-docs/scripts \
  skills/writing/pr-description/scripts tests
uv run --no-config --locked --project packages/context-engineering mypy --config-file mypy.ini \
  skills/writing/writing-check/scripts/writing_check.py
```

Writing Check findings are advisory evidence, so the release check accepts its
`findings` exit. Vale itself is required for that check: `unavailable` means the
catalog prerequisites are incomplete and fails the release check. The command
does not install Vale or download styles. CI downloads the official Vale v3.17.1
Linux archive, verifies SHA-256
`db947f89f2292e6a0381a61de155f6a5f5cb4cb460ca178ea412ef605559cefd`, and
proves `vale --version` before running the release check; the binary is not
shipped in this catalog.

For an isolated Context check, use the installed catalog package:

```bash
uv run --no-config --locked --project packages/context-engineering context-engineering check . --json
```

For an isolated Writing Check, run the complete catalog's bundled checker:

```bash
uv run --python 3.11 python \
  packages/writing-check/scripts/writing_check.py \
  --profile technical-doc --json README.md
```

Do not validate a Context skill from a selected-skill copy because that artifact
omits its required package. A copied Writing Check skill is self-contained; invoke
its included checker script and policy tree. See [installation](installation.md) for
both layouts.
