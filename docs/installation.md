# Installation

## Agent Skills

Install any canonical root skill with Vercel Skills:

```bash
npx skills add safurrier/skills --skill context-docs
npx skills add safurrier/skills --skill writing-check
```

Installing a skill copies its instructions only, not the sibling CLI package. Install its documented CLI when the workflow needs deterministic analysis.

## Writing suite

Writing and Writing Check are one suite. Install the independent Writing Check CLI from a trusted checkout (see the private GitHub source route below):

```bash
uv tool install ./packages/writing-check
writing-check --help
```

The package includes the reviewed Google Vale policy and pins the `vale` Python dependency. Vale downloads its executable on first use. No separate runtime-install or doctor command is required. The checker remains read-only and its findings remain advisory.

## Optional Context Engineering

Context Engineering is an optional suite. Install its independent CLI from a trusted checkout, then verify it is on `PATH`:

```bash
uv tool install ./packages/context-engineering
context-engineering --help
```

A Context skill reports its deterministic analysis as unavailable when this command is missing or incompatible; it does not search for another checkout or substitute manual analysis.

## Missing CLI with only selected skills installed

The catalog is currently a private GitHub repository. If you have access, `gh` authenticated for the private safurrier/skills repository, and `uv` installed, explicitly approve installing code from a trusted checkout before running these commands. Use a directory you control; inspect the checkout before installation. Do not run them automatically as part of a skill check.

```bash
checkout="$(mktemp -d)"
gh repo clone safurrier/skills "$checkout/skills"
# Inspect and trust "$checkout/skills" before installing either package.
uv tool install "$checkout/skills/packages/writing-check"       # if Writing Check is needed
writing-check --help
uv tool install "$checkout/skills/packages/context-engineering" # if Context Engineering is needed
context-engineering --help
```

Run only the install and help commands for the CLI you need. If `uv` or `gh` is absent, private-repository access is unavailable, clone/install fails (including network or dependency downloads), or help fails, report the dependency unavailable; do not claim its analysis ran. Installing Writing Check's Python dependency can fetch Vale from its GitHub release on first use; report `unavailable` or `execution_error` if that check cannot run.

Claude users can instead install the projected plugin:

```text
/plugin marketplace add safurrier/skills
/plugin install context-engineering@safurrier-skills
```

The plugin is a projection of the canonical Context skills and package, not their source of truth.

After package publication, the equivalent registry commands will be `uv tool install writing-check-cli` and `uv tool install context-engineering-cli`. Until then, use the trusted source-checkout commands above or the built-wheel commands in [reproducible validation](validation.md).

Run [reproducible validation](validation.md) from a source checkout when contributing.
