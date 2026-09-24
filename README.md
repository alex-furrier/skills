# skills

A portable catalog of engineering Agent Skills. Root `skills/` is canonical; the Claude plugin is a tested projection of its Context skills.

## Install

Install individual catalog skills with Vercel Skills:

```bash
npx skills add safurrier/skills --skill context-docs
npx skills add safurrier/skills --skill writing-check
```

Writing and Writing Check are one suite: install the `writing-check` skill and its CLI together. Context Engineering is an optional suite for deterministic repository analysis.

The packages are not yet published to a registry. From a trusted source checkout, install the suite and optional Context CLI with:

```bash
uv tool install ./packages/writing-check
writing-check --help
uv tool install ./packages/context-engineering
context-engineering --help
```

Installing selected skills alone does not include the CLI packages. If the CLI is missing and you have access to this private repository, follow the [authenticated GitHub checkout route](docs/installation.md#missing-cli-with-only-selected-skills-installed); it requires `gh`, `uv`, explicit install consent, and a trusted checkout. If the route or CLI check fails, report the dependency unavailable. Writing Check's pinned `vale` Python dependency downloads Vale on first use, so no second setup command is required. After package publication, the equivalent registry commands will be `uv tool install safurrier-writing-check` and `uv tool install safurrier-context-engineering`.

For Claude users, install the Context projection from this repository's marketplace:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

## Catalog

Writing skills, including Writing Check, are in `skills/writing/`. Optional Context Engineering skills are in `skills/context-engineering/`. The Claude plugin at `plugins/context-engineering/` is generated from the canonical Context skills and CLI package. Update it with:

```bash
python scripts/project_context_plugin.py
```

## Validate

```bash
python scripts/fast_check.py
```

The catalog is self-contained and makes no default account, credential, private-corpus, or hosted-service assumption. Writing Check findings are source-bound advisory observations, not proof of factuality or readiness.
