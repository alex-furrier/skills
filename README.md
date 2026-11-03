# Skills

Agent Skills for thinking, writing, and keeping useful context.

The aim is to keep good habits useful as agents get more capable: clarify the
problem, verify the evidence, explain it clearly, and retain what the next
session needs. These skills support engineering work, including code, through
reasoning and communication.

## What to install

| Suite | Use it when you need to… |
| --- | --- |
| [Thinking](docs/thinking.md) | Clarify a scattered request with Goalify, verify a claim with Research, or find missing domain expertise with experimental Blindspot. Each works independently. |
| [Writing](skills/writing/) | Draft or improve a README, PR description, or other prose, with advisory style checks. |
| [Context Engineering](skills/context-engineering/) | Keep AGENTS.md, docs, specifications, and decision records accurate; capture useful session knowledge. |

[Product Bet Shaping](skills/product/product-bet-shaping/SKILL.md) is a separate
skill for deciding whether an idea is worth pursuing and what to try first.

## Quick start

With Node.js 22.20 or newer, choose a suite:

```bash
npx skills@1.7.4 install alex-furrier/skills/skills/thinking --skill '*'
npx skills@1.7.4 install alex-furrier/skills/skills/writing --skill '*'
npx skills@1.7.4 install alex-furrier/skills/skills/context-engineering --skill '*'
```

Select your agent and installation scope at the prompts. Choose **Project** to
keep the install local to the current project. Each command selects every skill
in that suite. To install one skill instead, replace `'*'` with its name, such as
`goalify`. Avoid adding a second copy through another plugin.

Invocation depends on your agent: Codex uses `$goalify`, Claude Code uses
`/goalify`, and Pi uses `/skill:goalify`. Claude marketplace plugins namespace
the command, such as `/thinking:goalify`.

Thinking needs no companion CLI. Writing Check and Context Engineering workflows
also need their [companion CLIs](docs/installation.md). Installing the skills does
not install those packages. Style findings are advisory, not proof of factuality
or readiness.

See [installation](docs/installation.md) for agent paths, CLI setup, and the
Thinking and Context Engineering Claude plugins.

## Contribute

Root `skills/` is canonical. Update the sources, regenerate the affected plugin,
and run the checks:

```bash
python scripts/project_thinking_plugin.py
python scripts/project_context_plugin.py
python scripts/fast_check.py
```

See [architecture](docs/architecture.md) and [validation](docs/validation.md) for
ownership, provenance, and distribution checks.
