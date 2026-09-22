# Installation

## Agent Skills

Install any canonical root skill with Vercel Skills:

```bash
npx skills add safurrier/skills --skill context-docs
npx skills add safurrier/skills --skill writing-check
```

Installing a skill copies its instructions only. Install its documented CLI when the workflow needs deterministic analysis.

## Writing suite

Writing and Writing Check are one suite. Install the independent Writing Check CLI from a source checkout:

```bash
uv tool install ./packages/writing-check
writing-check --help
```

The package includes the reviewed Google Vale policy and pins the `vale` Python dependency. Vale downloads its executable on first use. No separate runtime-install or doctor command is required. The checker remains read-only and its findings remain advisory.

## Optional Context Engineering

Context Engineering is an optional suite. Install its independent CLI from a source checkout, then verify it is on `PATH`:

```bash
uv tool install ./packages/context-engineering
context-engineering --help
```

A Context skill reports its deterministic analysis as unavailable when this command is missing or incompatible; it does not search for another checkout or substitute manual analysis.

Claude users can instead install the projected plugin:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

The plugin is a projection of the canonical Context skills and package, not their source of truth.

After package publication, the equivalent registry commands will be `uv tool install safurrier-writing-check` and `uv tool install safurrier-context-engineering`. Until then, use the source-checkout commands above or the built-wheel commands in [reproducible validation](validation.md).

Run [reproducible validation](validation.md) from a source checkout when contributing.
