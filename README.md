# Skills

Agent Skills for thinking through a problem, writing something worth reading,
and keeping repository context useful.

The aim is to capture habits that remain useful as agents get better: clarify
what matters, check what is true, explain it clearly, and leave enough context
for the next person or session. These skills apply to engineering work, including
code, but focus on the reasoning and communication around it.

## What would you use?

| Start here | When it helps | What it does |
| --- | --- | --- |
| [Thinking](docs/thinking.md) | The request is scattered, an explanation is unverified, or the approach feels shallow. | `goalify` clarifies intent; `research` checks evidence; experimental `blindspot` finds and applies missing domain expertise. Use each independently. |
| [Writing](skills/writing/) | A README buries the point, a PR hides why it exists, or a draft sounds generic. | Draft and revise for the reader, preserve meaning, and collect advisory style checks. Includes README, PR, and general prose skills. |
| [Context Engineering](skills/context-engineering/) | Agents repeat the same investigation or repository docs no longer match the code. | Audit or update AGENTS.md, docs, SPEC/ADR contracts, and historical context; propose durable session captures. |
| [Product Bet Shaping](skills/product/product-bet-shaping/SKILL.md) | You need to decide whether an idea deserves time before building it. | Compare evidence, alternatives, opportunity cost, and the smallest useful next commitment. Installed separately from Thinking. |

Thinking and Context Engineering have Claude marketplace plugins. Writing and
Product Bet Shaping are available as individual catalog skills, not marketplace
plugins. Install only what you need; there is no required sequence.

## Quick start

This repository is currently **private**. You need existing repository access;
these commands do not grant access. Use Node.js 22.20 or newer for the tested
Skills CLI version.

From the project where you want the skill, install Goalify for Codex:

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.4 add git@github.com:alex-furrier/skills.git \
  --skill goalify --agent codex --copy
```

This uses your existing GitHub SSH access and copies instructions and adjacent
resources into the project's `.agents/skills/goalify/`. It does not install a
companion CLI or change your global profile. Review the installer prompt, then ask
your agent: **“Use goalify to untangle this request: …”**

For all three Thinking skills, replace `--skill goalify` with
`--skill goalify research blindspot`. Blindspot is experimental. Avoid installing
a second copy if your agent already gets these skills from another plugin.

Claude users can install either marketplace plugin:

```text
/plugin marketplace add alex-furrier/skills
/plugin install thinking@safurrier-skills
/plugin install context-engineering@safurrier-skills
```

Choose the plugin you need. See [installation](docs/installation.md) for other
agents, HTTPS access, companion CLIs, and source-checkout options.

## A few examples

These are illustrative sketches of the intended workflow, not measured outputs
or evidence that a skill improves results.

- **Goalify:** “Customers notice failed jobs before we do. We need dashboards,
  alerts, maybe a weekly report.” → “Notice failed jobs before customers do;
  the delivery format is undecided.”
- **Research:** “This flag probably enables retries.” → “Trace the flag to its
  caller, cite the retry condition, and separate verified behavior from unknowns.”
- **README Improver:** A page opens with installation flags and a directory list.
  → It opens with what the tool does, when to use it, and one verified first run.
- **Context Review:** A PR changes a configuration default. → Check whether the
  documented default and agent guidance need updating; route any change to their owner.

## Dependencies and limits

Thinking and Product Bet Shaping need no companion CLI. Writing and Writing
Check form one suite: install the `writing-check` skill and its CLI together.
Context Engineering is optional and uses its own deterministic analysis CLI.
Installing selected skills does not include these packages. With explicit
install consent, install only the published CLI you need:

```bash
uv tool install writing-check-cli==1.0.1
writing-check --help
uv tool install context-engineering-cli==2.6.1
context-engineering --help
```

The pinned releases are [published on PyPI](docs/installation.md); a trusted
source checkout is an optional fallback. Never install automatically. If an
install or CLI check fails, report that dependency unavailable rather than
claiming analysis ran. Writing Check's pinned `vale` dependency downloads Vale
on first use.

Writing Check findings are source-bound advisory observations, not proof of
factuality or readiness. PR descriptions preserve the upstream `pr-risk-note`
assessment in a compact `Risk` section, or report that it was not supplied;
Writing Check does not classify risk from prose. The risk skill also works alone
without a CLI or hosted service.

The catalog has no default account, credential, private-corpus, or hosted-service
dependency. Packaging checks establish portability and parity, not improved
outcomes or lasting usefulness as models change.

## Contribute

Root `skills/` is canonical. Claude plugins are tested projections, not separate
editable sources. After changing the relevant canonical sources, regenerate:

```bash
python scripts/project_thinking_plugin.py
python scripts/project_context_plugin.py
python scripts/fast_check.py
```

Thinking includes exactly Blindspot, Research, and Goalify; Plan and Product Bet
Shaping are outside that plugin. See [Thinking](docs/thinking.md),
[architecture](docs/architecture.md), and [validation](docs/validation.md) for
ownership, provenance, and the complete checks.
