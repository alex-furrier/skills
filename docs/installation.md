# Installation

## Agent Skills

This repository is private; installation requires existing GitHub access.
The portable skills themselves need no particular account, but fetching this
repository does. Sharing an install command does not grant access.

With Node.js 22.20 or newer, install selected skills into the current project:

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.4 add git@github.com:alex-furrier/skills.git \
  --skill goalify research blindspot --agent codex --copy
```

Use `--skill goalify` for one skill. Blindspot remains experimental; it is not
required by Research or Goalify. For Writing or Context, select a catalog name
such as `writing-check` or `context-docs` instead. Avoid duplicate installations
when your agent already receives the same skill through a managed plugin.

The command uses existing SSH authentication, prompts before installation, and
copies each skill with its adjacent resources into `.agents/skills/<name>/`.
It also writes project installer metadata in a skills-lock.json file. Without `--global`, it does not
install skills into your user profile. `--agent claude-code` selects Claude's
project scope instead. See the [Skills CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)
for other supported agents and their paths. `DISABLE_TELEMETRY=1` disables the
CLI's telemetry and security-audit requests; it is appropriate for this private source.

If GitHub HTTPS access is already configured, the source can instead be
the GitHub shorthand alex-furrier/skills. An authorized local checkout is another source:

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.4 add /absolute/path/to/skills \
  --skill goalify --agent codex --copy
```

Run `npx skills@1.7.4 list --agent codex` from the project to inspect installed
skills, then select the named skill in your agent. Installing skills includes
instructions and adjacent resources, not their sibling CLI packages.

For public installation later, an explicitly authorized public distribution
must contain the intended skills, references, licenses and provenance. The
current private repository is accessible only to authorized users. Neither
these instructions nor the marketplace entry changes that boundary.

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

For a source install, you need access to the private GitHub repository, `gh` authenticated for it, and `uv` installed. Explicitly approve installing code from a trusted checkout before running these commands. Use a directory you control; inspect the checkout before installation. Do not run them automatically as part of a skill check.

```bash
checkout="$(mktemp -d)"
gh repo clone alex-furrier/skills "$checkout/skills"
# Inspect and trust "$checkout/skills" before installing either package.
uv tool install "$checkout/skills/packages/writing-check"       # if Writing Check is needed
writing-check --help
uv tool install "$checkout/skills/packages/context-engineering" # if Context Engineering is needed
context-engineering --help
```

Run only the install and help commands for the CLI you need. If `uv` is absent, the registry install fails, or help fails, report the dependency unavailable; do not claim its analysis ran.

For the optional source route, the same applies if `gh` or private-repository access is unavailable or clone/install fails (including network or dependency downloads).

Installing Writing Check's Python dependency can fetch Vale from its GitHub release on first use; report `unavailable` or `execution_error` if that check cannot run.

Claude users can instead install the projected plugin:

```text
/plugin marketplace add alex-furrier/skills
/plugin install context-engineering@safurrier-skills
```

The plugin is a projection of the canonical Context skills and package, not their source of truth.

Run [reproducible validation](validation.md) from a source checkout when contributing.
