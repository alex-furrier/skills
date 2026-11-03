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

Invocation depends on the agent: Codex uses `$write`, Claude Code uses `/write`,
and Pi uses `/skill:write` for the Writing router. Claude marketplace plugins
namespace their commands, such as `/thinking:goalify`. Writing is a catalog suite,
not a Claude marketplace plugin.

Thinking needs no companion CLI. Writing Check and Context Engineering workflows
also need their [companion CLIs](docs/installation.md). Installing the skills does
not install those packages. Style findings are advisory, not proof of factuality
or readiness.

See [installation](docs/installation.md) for agent paths, CLI setup, and the
Thinking and Context Engineering Claude plugins.

## Use it

After installing the Writing suite and its [companion CLI](docs/installation.md#writing-suite),
start with [write](skills/writing/write/SKILL.md): “Clean up this explanation without changing its meaning.”
The router selects the destination skill and checks the final candidate. It can
offer an optional Anti-LLM Writer pass when the draft reads synthetic.

For a specific destination, use its skill directly:

- PR description → [pr-description](skills/writing/pr-description/SKILL.md).
- PR risk assessment → [pr-risk-note](skills/writing/pr-risk-note/SKILL.md).
- README → [readme-improver](skills/writing/readme-improver/SKILL.md).
- Explanation or handoff → [user-facing-response](skills/writing/user-facing-response/SKILL.md).
- General drafting → [writing-core](skills/writing/writing-core/SKILL.md).

The router and these examples describe the skill contracts, not end-to-end agent
tests. Check findings remain advisory. Installing skills grants no permission to
publish, post, or merge.

### Optional automatic checks

Only if the project wants checks after material prose edits, copy this guidance
into its `AGENTS.md` or `CLAUDE.md` after installing the Writing suite and CLI:

```markdown
After material prose changes, follow the installed Writing Check skill.
Skip typo-only edits and generated or vendored text.
Check the exact final candidate with its destination profile; recheck edits.
Fix worthwhile findings; keep justified wording. Scores are advisory.
Report missing tools instead of claiming a check ran.
```

This guidance is optional. It sets no hook or enforcement gate. Installing the
suite never adds it to project instructions.

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
