# skills

A portable catalog of engineering skills. Context engineering is a complete Claude plugin; Writing skills are individually installable catalog skills.

## Install

### Context engineering plugin

Install the `context-engineering` plugin from this repository's Claude marketplace:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

The marketplace source is `./plugins/context-engineering`, so its skills and shared CLI are copied together. Retain the complete plugin directory; a copied Context skill alone cannot run deterministic analysis.

Context commands always use the plugin-local project:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering <subcommand> ...
```

`uv` and Python 3.11+ are required. A missing CLI is a fail-fast error, not a fallback to manual inspection.
Verify the installed plugin retains `LICENSE`, `provenance.json`, `cli/pyproject.toml`, and `skills/`, then run `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering --help`.

### Writing skills

Ordinary Writing skills remain under `skills/writing/`. Install the self-contained Writing Check skill with the Skills CLI:

```bash
npx skills add safurrier/skills --skill writing-check
```

Skills CLI copies a selected skill directory and cannot atomically install Context, whose CLI is a sibling plugin asset. `skills.sh` is a discovery site, not the installer. Writing Check includes its checker, Vale policy, vendored Google rules, and license; Vale remains an external required executable and its findings are advisory.

See [installation](docs/installation.md) for verification and boundaries.

## Catalog

### Context

`context-agents-md`, `context-improve`, `context-contracts`, `context-backfill`, `context-docs`, `context-review`, `repository-context-refresh`, and `session-capture` are in `plugins/context-engineering/skills/`.

### Writing

`writing-core`, `writing-check`, `anti-llm-writer`, `user-facing-response`, `readme-improver`, and `pr-description` remain in `skills/writing/`.

## Validate

```bash
python scripts/fast_check.py
uv run --no-config --locked --no-dev --project plugins/context-engineering/cli context-engineering references . --json
uv run --python 3.11 python skills/writing/writing-check/scripts/writing_check.py --profile technical-doc README.md
```

The Writing Check result is exact-input-bound advisory evidence, not proof of factuality or readiness.

## Boundaries

No default skill assumes a particular account, credential, home directory, task tracker, external knowledge destination, or hosted service. See [contributing](CONTRIBUTING.md), [provenance](provenance.json), and [third-party notices](THIRD_PARTY_NOTICES.md).
