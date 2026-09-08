# Installation

Install this catalog as one complete checkout or source archive. Do not use a
skill-only installer or copy a chosen skill directory for Context skills or
Writing Check: those paths omit required catalog packages or vendored policy
assets.

## Complete catalog checkout

Place the full repository contents under one catalog root, preserving both
`skills/` and `packages/`. Before configuring an agent, verify the required
layout:

```bash
test -f <catalog-root>/packages/context-engineering/pyproject.toml
test -d <catalog-root>/packages/writing-check/vale/styles/GoogleDocs
test -d <catalog-root>/skills/context
test -d <catalog-root>/skills/writing
```

Configure the compatible agent to discover skills from
`<catalog-root>/skills`. A plugin manager is suitable only when its installed
artifact preserves that complete layout; verify the four paths above in the
installed location before relying on Context skills or Writing Check.

## Skill-only installer boundary

Do not use `npx skills add safurrier/skills` for this catalog. The locally
inspected Skills CLI v1.5.18 copies each discovered skill directory into an
agent target, not sibling catalog packages. Its `installSkillForAgent` source
calls `copyDirectory(skill.path, ...)`, so it cannot preserve the required
`packages/` layout. This conclusion is recorded from local source inspection;
no network installation was run.

## Prerequisites

Obtain `uv` and Vale through the package-management or deployment mechanism
approved for the target environment. This catalog does not prescribe or verify
an external registry or installer. Confirm both executables before running the
corresponding workflows:

```bash
uv --version
vale --version
```

Context workflows require `uv`, Python 3.11+, and
`packages/context-engineering`. Run deterministic analysis with:

```bash
uv run --project <catalog-root>/packages/context-engineering \
  context-engineering <subcommand> ...
```

Writing Check requires Vale and the bundled Google Vale rules at
`packages/writing-check/vale/`. Its findings are advisory, but a missing Vale
executable is unavailable evidence rather than a replacement-policy result.

Run [reproducible validation](validation.md) from the catalog root after
installation.
