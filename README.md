# Skills

A portable catalog of engineering Agent Skills. Root `skills/` is canonical. Claude plugins are tested projections of their canonical skills.

## Install

Install individual catalog skills with Vercel Skills if you have access to this private repository:

```bash
npx skills add alex-furrier/skills --skill context-docs
npx skills add alex-furrier/skills --skill writing-check
```

Writing and Writing Check are one suite: install the `writing-check` skill and its CLI together. Context Engineering is an optional suite for deterministic repository analysis.

PR descriptions preserve the upstream `pr-risk-note` assessment in a compact
`Risk` section, or report that it was not supplied. The risk skill works on its
own without a CLI or hosted-service dependency; Writing Check does not classify
PR risk from prose.

Installing selected skills alone does not include their CLI packages. With explicit install consent, install the published CLIs you need from PyPI using `uv`:

```bash
uv tool install writing-check-cli==1.0.1
writing-check --help
uv tool install context-engineering-cli==2.6.1
context-engineering --help
```

Writing Check 1.0.1 and Context Engineering 2.6.1 are [published on PyPI](docs/installation.md). A [trusted source checkout](docs/installation.md#trusted-source-checkout-fallback) remains an optional fallback.

- Never install automatically.
- If installation or the CLI check fails, report the dependency unavailable rather than claiming analysis ran.
- Writing Check's pinned `vale` Python dependency downloads Vale on first use, so no second setup command is required.

For Claude users, install the Context projection from this repository's marketplace:

```text
/plugin marketplace add alex-furrier/skills
/plugin install context-engineering@safurrier-skills
```

## Catalog

[Thinking](docs/thinking.md) contains independent `blindspot`, `research` and
`goalify` skills under `skills/thinking/`, with a generated `plugins/thinking/`
distribution. `product-bet-shaping` lives separately under `skills/product/` and
is installed on its own. Plan is not bundled. Thinking requires no CLI package.

Writing skills, including Writing Check, are in `skills/writing/`. Optional Context Engineering skills are in `skills/context-engineering/`. The Claude plugin at `plugins/context-engineering/` is generated from the canonical Context skills and CLI package. Update it with:

```bash
python scripts/project_context_plugin.py
```

## Validate

```bash
python scripts/fast_check.py
```

The catalog is self-contained and makes no default account, credential, private-corpus, or hosted-service assumption. Writing Check findings are source-bound advisory observations, not proof of factuality or readiness.
