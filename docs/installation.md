# Installation

## Agent Skills

Install any canonical root skill with Vercel Skills:

```bash
npx skills add safurrier/skills --skill context-docs
npx skills add safurrier/skills --skill writing-check
```

Installing a skill copies its instructions only. Install its documented CLI when the workflow needs deterministic analysis.

## Context Engineering

Install the independent Context CLI, then verify it is on `PATH`:

```bash
uv tool install safurrier-context-engineering
context-engineering --help
```

A Context skill reports its deterministic analysis as unavailable when this command is missing or incompatible; it does not search for another checkout or substitute manual analysis.

Claude users can instead install the projected plugin:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

The plugin is a projection of the canonical Context skills and package, not their source of truth.

## Writing Check

Install the independent Writing Check CLI:

```bash
uv tool install safurrier-writing-check
writing-check --help
```

The package includes the reviewed Google Vale policy and pins the `vale` Python dependency. Vale downloads its executable on first use. No separate runtime-install or doctor command is required. The checker remains read-only and its findings remain advisory.

Run [reproducible validation](validation.md) from a source checkout when contributing.
