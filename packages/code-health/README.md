# Code Health Review CLI

`code-health` collects repository metric deltas for the Code Health Review skill.
It supports Ruff, Clippy, ESLint, and golangci-lint, but installs no analyzers.
Missing analyzers are reported as evidence gaps. Metrics support human review;
they do not establish architecture or maintainability quality.

Requires Python 3.11 or newer. From a trusted source checkout, run:

```bash
uv run --frozen --no-dev --project packages/code-health code-health --help
uv run --frozen --no-dev --project packages/code-health code-health diff . --base main --format json
```

The package is not published to PyPI yet. See the repository's
[installation guide](https://github.com/alex-furrier/skills/blob/main/docs/installation.md#code-quality-suite)
for setup and limitations.
