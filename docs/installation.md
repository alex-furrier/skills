# Installation

## Context engineering Claude plugin

The root marketplace manifest publishes `context-engineering` from `./plugins/context-engineering`. Install it through Claude:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

Its local closure is:

```bash
test -f <context-plugin-root>/.claude-plugin/plugin.json
test -f <context-plugin-root>/LICENSE
test -f <context-plugin-root>/provenance.json
test -f <context-plugin-root>/cli/pyproject.toml
test -d <context-plugin-root>/cli/src/context_engineering
test -d <context-plugin-root>/skills
```

Configure Claude to discover the plugin's `skills/` directory. Verify the installed CLI with `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering --help`. Context workflows require `uv`, Python 3.11+, and the plugin-local CLI:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli \
  context-engineering <subcommand> ...
```

Do not copy a Context skill alone. A selected-skill installer does not retain the sibling CLI project, and Context commands must report that deterministic verification is unavailable rather than locate another checkout.

## Writing skills through Skills CLI

Writing skills remain in the public `skills/writing/` catalog. Install Writing Check explicitly:

```bash
npx skills add safurrier/skills --skill writing-check
```

Run that command with `DISABLE_TELEMETRY=1` when telemetry must be disabled. Skills CLI discovery may list Context `SKILL.md` files, but it copies selected skill directories and cannot atomically install Context. `skills.sh` is discovery/ranking infrastructure, not the installer.

A copied Writing Check directory is supported and must contain:

```bash
test -f <writing-check-skill>/scripts/writing_check.py
test -d <writing-check-skill>/vale/styles/GoogleDocs
test -f <writing-check-skill>/vale/vendor/Google-LICENSE
```

Writing Check requires external Vale; its bundled policy is self-contained and its findings remain advisory.

## Prerequisites and validation

Obtain `uv` and Vale through the environment's approved package-management mechanism. This catalog does not install either executable.

```bash
uv --version
vale --version
```

Run [reproducible validation](validation.md) from this source checkout after installation.
