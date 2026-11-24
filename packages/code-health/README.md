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

### Shared decision excerpts

Alongside native analyzer output, scan and diff show pairs of tracked source files
**within the requested path** that share six literal lines with a branch-like
line and flow-control keyword. This standard-library check runs on Python, Rust,
Go and JavaScript/TypeScript without installing language toolchains.

A diff shows a pair only if a matching excerpt intersects added or modified lines
since the merge base, including the working tree. A moved or restored block can
also match. A separate *one-sided edit* means an edit removed a matching excerpt
from one side while another, unchanged file still contains it. The report shows
the old lines, the replacement hunk and the peer. Pure removals and renames
do not count as one-sided edits. Ask whether the sites own the same policy.

This is text, not an AST: parallel implementations, inline tests and example
strings can match. Renamed, differently formatted or semantically equivalent
logic can be missed. No count contributes to a quality verdict or finding delta.

Each category retains one example per file pair (up to 12 pairs). Frequent
boilerplate and conventionally named tests/generated sources are excluded.
Truncation and unreadable inputs appear in `shared_decisions.skipped`. Budgets
are 512 KB per file, 12 MB or 2,000 file reads total, 40,000 qualifying windows,
60 changed files and 128 diff hunks per changed file. Narrow the path if capped.
