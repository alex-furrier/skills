# Code Health Review CLI

`code-health` collects repository metric deltas for the Code Health Review skill.
It supports Ruff, Clippy, ESLint, and golangci-lint, but installs no analyzers.
Missing analyzers are reported as evidence gaps. Metrics support human review;
they do not establish architecture or maintainability quality.

Requires Python 3.11 or newer. From the root of a trusted checkout of
[alex-furrier/skills](https://github.com/alex-furrier/skills), run:

```bash
uv run --frozen --no-dev --project packages/code-health code-health --help
uv run --frozen --no-dev --project packages/code-health code-health diff /path/to/repo --base main --format json
```

See the
[installation guide](https://github.com/alex-furrier/skills/blob/main/docs/installation.md#code-quality-suite)
for install options and limitations.
