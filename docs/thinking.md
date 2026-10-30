# Thinking and Product Bet Shaping

Thinking contains three independently usable skills:

| Skill | Use it for | Boundary |
| --- | --- | --- |
| `goalify` | Distilling scattered intent into a useful goal | A standalone request ends at the synthesis |
| `research` | Verifying code, systems and consequential factual premises | Findings need inspected evidence and explicit uncertainty |
| `blindspot` | Finding and applying missing domain expertise | Experimental; strengthen the current task without expanding its authority |

Use any one directly. Research can change a goal, Goalify can clarify one, and
Blindspot can expose a missing method. These are optional connections, not a
required sequence. Planning and implementation remain with the task's existing
owner. Named helpers are optional integrations; no particular model, provider,
CLI, account, private source or delegated agent is required.

## Install or try Thinking

This repository is private. These routes require existing repository access;
sharing a link does not grant access or change repository visibility.

Install an individual skill with the host-compatible Skills installer:

```bash
npx skills add alex-furrier/skills --skill blindspot
npx skills add alex-furrier/skills --skill research
npx skills add alex-furrier/skills --skill goalify
```

Or use the Claude marketplace plugin:

```text
/plugin marketplace add alex-furrier/skills
/plugin install thinking@safurrier-skills
```

From an authorized checkout or a copy of `plugins/thinking`, try it without a
persistent install:

```bash
claude --plugin-dir /absolute/path/to/thinking
pi --skill /absolute/path/to/thinking/skills/research
```

For a source checkout, replace `/absolute/path/to/thinking` with its
`plugins/thinking` directory. Select a named skill in the session. Other hosts
can import each canonical SKILL.md with its adjacent references, LICENSE and
provenance.json through their supported skill mechanism. Installation is an
explicit action, not part of running a skill. The plugin does not set a default
profile or install a CLI. No PyPI release is needed for this instruction-only
plugin; an immutable reviewed catalog commit identifies a distribution.

## Product Bet Shaping is separate

`skills/product/product-bet-shaping` is a standalone portable skill. It helps
triage, discover, shape or review a bounded product bet using evidence,
alternatives, opportunity cost and outcome checks. It does not change approved
priorities or authorize implementation.

```bash
npx skills add alex-furrier/skills --skill product-bet-shaping
```

This skill and Plan are outside the Thinking plugin. Product Bet Shaping can be
imported alone with all adjacent resources; it needs no Thinking installation.

## Source ownership and maintenance

`skills/thinking/` and `skills/product/` are canonical. Edit them here.
`plugins/thinking/` is a generated, independently copyable distribution:

```bash
python scripts/project_thinking_plugin.py
python scripts/project_thinking_plugin.py --check
python scripts/fast_check.py
```

The generator copies exactly Blindspot, Research and Goalify, including references,
licenses and per-skill input provenance. It adds plugin metadata, a usage guide,
license and plugin-scoped provenance. Catalog tests check an independent copied
plugin and each individual skill, reject stale or altered payloads, and exercise
the generator with only the catalog source closure. They never import Dots.

The skills originated as same-author portable adaptations from Dots; per-skill
provenance identifies the exact input revision and SHA-256 hashes. Referenced
third-party articles and methods remain attributed; the catalog license does not
claim rights to those linked works. No private evaluation corpus or session
transcript is bundled. Existing historical trials retain their original identity.

Packaging and source checks establish portability and parity. They do not show
that a skill improves results. Blindspot remains experimental, and bounded Research
comparisons do not establish a general quality or speed gain. Detailed evaluation
reports have separate owners and are not runtime dependencies.
