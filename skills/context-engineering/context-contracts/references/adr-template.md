# Lean ADR template

Use the repository's existing filename, metadata, and index convention. The
fields below are the portable minimum checked by the CLI.

```markdown
# <Decision title>

Status: Proposed
Date: YYYY-MM-DD

## Context

<Verified pressure or constraint that required a decision.>

## Decision

<The chosen lasting direction.>

## Consequences

<Important tradeoffs and follow-up constraints.>
```

For replacement records, change the old record to `Status: Superseded` and add
`Superseded by: <relative-adr-path>`. Keep links relative and update an existing
ADR index. Do not create an index solely to satisfy this template.
