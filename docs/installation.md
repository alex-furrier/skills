# Installation

## Agent Skills

Install any canonical root skill with Vercel Skills:

```bash
npx skills add alex-furrier/skills --skill context-docs
npx skills add alex-furrier/skills --skill writing-check
```

Installing a skill copies its instructions only, not the sibling CLI package. Install its documented CLI when the workflow needs deterministic analysis.

## Writing suite

Writing and Writing Check are one suite. With explicit consent, install the [published Writing Check CLI 1.0.0](https://pypi.org/project/writing-check-cli/):

```bash
uv tool install writing-check-cli==1.0.0
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

If you prefer a source install and have access to the private GitHub repository, `gh` authenticated for it, and `uv` installed, explicitly approve installing code from a trusted checkout before running these commands. Use a directory you control; inspect the checkout before installation. Do not run them automatically as part of a skill check.

```bash
checkout="$(mktemp -d)"
gh repo clone alex-furrier/skills "$checkout/skills"
# Inspect and trust "$checkout/skills" before installing either package.
uv tool install "$checkout/skills/packages/writing-check"       # if Writing Check is needed
writing-check --help
uv tool install "$checkout/skills/packages/context-engineering" # if Context Engineering is needed
context-engineering --help
```

Run only the install and help commands for the CLI you need. If `uv` is absent, the registry install fails, or help fails, report the dependency unavailable; do not claim its analysis ran. For the optional source route, the same applies if `gh` or private-repository access is unavailable or clone/install fails (including network or dependency downloads). Installing Writing Check's Python dependency can fetch Vale from its GitHub release on first use; report `unavailable` or `execution_error` if that check cannot run.

Claude users can instead install the projected plugin:

```text
/plugin marketplace add alex-furrier/skills
/plugin install context-engineering@safurrier-skills
```

The plugin is a projection of the canonical Context skills and package, not their source of truth.

Run [reproducible validation](validation.md) from a source checkout when contributing.
