# skills

A portable catalog of engineering Agent Skills. Root `skills/` is canonical; the Claude plugin is a tested projection of its Context skills.

## Install

Install individual catalog skills with Vercel Skills:

```bash
npx skills add safurrier/skills --skill context-docs
npx skills add safurrier/skills --skill writing-check
```

Context skills require the separately installable CLI:

```bash
uv tool install safurrier-context-engineering
context-engineering --help
```

Writing Check is a separately installable CLI. Its pinned `vale` Python dependency downloads Vale on first use, so no second setup command is required:

```bash
uv tool install safurrier-writing-check
writing-check --help
```

For Claude users, install the Context projection from this repository's marketplace:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

## Catalog

Context skills are in `skills/context-engineering/`; Writing skills are in `skills/writing/`. The Claude plugin at `plugins/context-engineering/` is generated from the canonical Context skills and CLI package. Update it with:

```bash
python scripts/project_context_plugin.py
```

## Validate

```bash
python scripts/fast_check.py
```

The catalog is self-contained and makes no default account, credential, private-corpus, or hosted-service assumption. Writing Check findings are source-bound advisory observations, not proof of factuality or readiness.
