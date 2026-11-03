# Installation

## Install a suite

Use Node.js 22.20 or newer. Each command selects all skills in one canonical suite:

```bash
npx skills@1.7.4 install alex-furrier/skills/skills/thinking --skill '*'
npx skills@1.7.4 install alex-furrier/skills/skills/writing --skill '*'
npx skills@1.7.4 install alex-furrier/skills/skills/context-engineering --skill '*'
```

`install` is an alias for `add` in Skills CLI 1.7.4. The repository subdirectory
limits discovery to that suite, and the quoted wildcard selects its skills.
There is no skill named `thinking` or `writing`: suite selection uses a source
path, not a skill name. No wrapper or extra package is required.

Select your agent and scope at the prompts. Choose **Project** for a local install;
**Global** affects your user configuration. Depending on the selected agents,
the installer may offer symlinks or copies. To specify a target without prompts, use an agent ID from the table
below with `--copy --yes`; this uses project scope when `--global` is absent.
For example:

```bash
npx skills@1.7.4 install alex-furrier/skills/skills/thinking \
  --skill '*' --agent claude-code --copy --yes
```

## Agent paths and invocation

The suite contents are the same; installation paths and command syntax differ:

| Agent | Installer ID | Project skill directory | Invoke an individual Goalify skill |
| --- | --- | --- | --- |
| Codex | `codex` | `.agents/skills/` | `$goalify` |
| Claude Code | `claude-code` | `.claude/skills/` | `/goalify` |
| Pi | `pi` | `.agents/skills/` | `/skill:goalify` |

Claude plugin skills have a namespace: use `/thinking:goalify` for the Thinking
marketplace plugin. Open your agent in the installed project; start a new session
or reload skills if needed. See the host documentation for
[Codex](https://developers.openai.com/codex/skills/),
[Claude Code](https://code.claude.com/docs/en/skills), and
[Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md).
The [Skills CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)
covers other supported agents and their paths.

Run `npx skills@1.7.4 list` from the project to inspect installed skills.
Installation includes instructions and adjacent resources, not sibling CLI
packages. Avoid duplicate installs if another plugin already supplies a skill.

## Install an individual skill

Use the same source path with a named skill, or select it from the full catalog:

```bash
npx skills@1.7.4 install alex-furrier/skills --skill goalify
npx skills@1.7.4 install alex-furrier/skills --skill product-bet-shaping
```

Blindspot is experimental and independent of Research and Goalify. Product Bet
Shaping and Plan are outside Thinking; Plan is not bundled in this catalog.

## Writing suite

Writing and Writing Check are one suite. With explicit consent, install the [published Writing Check CLI 1.0.1](https://pypi.org/project/writing-check-cli/):

```bash
uv tool install writing-check-cli==1.0.1
writing-check --help
```

The package includes the reviewed Google Vale policy and pins the `vale` Python dependency. Vale downloads its executable on first use. No separate runtime-install or doctor command is required. The checker remains read-only and its findings remain advisory.

## Optional Context Engineering

Context Engineering is an optional suite. With explicit consent, install the [published Context Engineering CLI 2.6.1](https://pypi.org/project/context-engineering-cli/), then verify it is on `PATH`:

```bash
uv tool install context-engineering-cli==2.6.1
context-engineering --help
```

A Context skill reports its deterministic analysis as unavailable when this command is missing or incompatible; it does not search for another checkout or substitute manual analysis.

## Trusted source checkout fallback

For a source install, you need Git and `uv` installed. Explicitly approve installing code from a trusted checkout before running these commands. Use a directory you control; inspect the checkout before installation. Do not run them automatically as part of a skill check.

```bash
checkout="$(mktemp -d)"
git clone https://github.com/alex-furrier/skills.git "$checkout/skills"
# Inspect and trust "$checkout/skills" before installing either package.
uv tool install "$checkout/skills/packages/writing-check"       # if Writing Check is needed
writing-check --help
uv tool install "$checkout/skills/packages/context-engineering" # if Context Engineering is needed
context-engineering --help
```

Run only the install and help commands for the CLI you need. If `uv` is absent, the registry install fails, or help fails, report the dependency unavailable; do not claim its analysis ran.

For the optional source route, the same applies if Git is unavailable or clone/install fails (including network or dependency downloads).

Installing Writing Check's Python dependency can fetch Vale from its GitHub release on first use; report `unavailable` or `execution_error` if that check cannot run.

## Claude marketplace plugins

Thinking and Context Engineering also have projected plugins:

```text
/plugin marketplace add alex-furrier/skills
/plugin install thinking@safurrier-skills
/plugin install context-engineering@safurrier-skills
```

Choose the plugin you need. These are projections of canonical sources, not their
source of truth. Writing is available as catalog skills, not a marketplace plugin.

PR descriptions preserve the upstream `pr-risk-note` assessment in a compact
`Risk` section, or report that it was not supplied. Writing Check does not infer
PR risk from prose; the risk skill works independently without a companion CLI.
The catalog has no default account, credential, private-corpus, or hosted-service
dependency. Packaging checks establish portability and parity, not improved outcomes.

Run [reproducible validation](validation.md) from a source checkout when contributing.
