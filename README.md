# skills

An opinionated, portable collection of engineering skills for agents and their operators. It pairs durable-context workflows with precise writing workflows. Skills remain the product; the catalog includes deterministic Context analysis and source-bound Writing Check evidence where prose alone is not enough.

## Install

Install the complete catalog checkout or source archive for Context skills because
skill-only installers omit their required sibling package. Writing Check can install
on its own because its skill directory contains the checker and policy assets. See
[installation](docs/installation.md) for the required layouts and prerequisites.

### Required dependencies

- **Context skills:** install `uv` and retain `packages/context-engineering` at the catalog root. Run deterministic analysis with `uv run --no-config --locked --no-dev --project <catalog-root>/packages/context-engineering context-engineering <subcommand> ...`. A missing `uv` executable or Context package is a fail-fast error for workflows that require deterministic analysis; it is not a read-only fallback.
- **Writing Check:** install Vale and retain the `vale/` directory bundled with either the complete catalog or the standalone skill. Writing Check uses vendored Google Vale v0.7.1 rules plus readability evidence; findings remain advisory, never an automatic gate.

This source checkout uses Python 3.11+.

## Catalog

### Context

`context-agents-md`, `context-improve`, `context-contracts`, `context-backfill`, `context-docs`, `context-review`, `repository-context-refresh`, and `session-capture` help teams inspect, propose, and maintain durable repository knowledge.

### Writing

`writing-core`, `writing-check`, `anti-llm-writer`, `user-facing-response`, `readme-improver`, and `pr-description` help produce clear technical prose while preserving facts, commands, warnings, and authority boundaries.

## Validate

```bash
python scripts/fast_check.py
uv run --no-config --locked --no-dev --project packages/context-engineering context-engineering references . --json
uv run --python 3.11 python packages/writing-check/scripts/writing_check.py --profile technical-doc README.md
```

The last command returns advisory observations. It is exact-input-bound: its digest identifies the checked bytes but does not prove factuality, quality, or readiness.

## Boundaries

No default skill assumes a particular account, credential, home directory, task tracker, external knowledge destination, or hosted service. Required catalog dependencies fail clearly when missing; optional integrations must say what happens when unavailable. See [contributing](CONTRIBUTING.md), [provenance](provenance.json), and [third-party notices](THIRD_PARTY_NOTICES.md).
