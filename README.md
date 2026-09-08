# skills

An opinionated, portable collection of engineering skills for agents and their operators. It pairs durable-context workflows with precise writing workflows. Skills remain the product; two small, dependency-free tools collect deterministic evidence where prose alone is not enough.

## Install

With the Skills CLI:

```bash
npx skills add safurrier/skills
```

For Claude Code, install this repository as a plugin; its manifest exposes the complete catalog. Other compatible agents can copy a chosen skill directory and its referenced files. `writing-check` bundles its checker. When copying a Context skill that requests deterministic evidence, preserve this relative layout:

```text
<catalog-root>/
├── <agent-dir>/skills/context-docs/
└── packages/context-engineering/
```

Add `<catalog-root>/packages/context-engineering` to `PYTHONPATH`. Without that package, the skill must report unavailable evidence and continue with inspection. This source checkout uses Python 3.11+; Vale is optional.

## Catalog

### Context

`context-agents-md`, `context-improve`, `context-contracts`, `context-backfill`, `context-docs`, `context-review`, `repository-context-refresh`, and `session-capture` help teams inspect, propose, and maintain durable repository knowledge.

### Writing

`writing-core`, `writing-check`, `anti-llm-writer`, `user-facing-response`, `readme-improver`, and `pr-description` help produce clear technical prose while preserving facts, commands, warnings, and authority boundaries.

## Validate

```bash
./scripts/fast-check.sh
PYTHONPATH=packages/context-engineering python3 -m context_engineering references . --json
python3 packages/writing-check/scripts/writing_check.py --profile technical-doc README.md
```

The last command returns advisory observations. It is exact-input-bound: its digest identifies the checked bytes but does not prove factuality, quality, or readiness.

## Boundaries

No default skill assumes a particular account, credential, home directory, task tracker, external knowledge destination, or hosted service. Optional integrations must say what happens when unavailable. See [contributing](CONTRIBUTING.md) and [provenance](provenance.json).
