# Context review routing

## Ownership tests

- **SPEC.md**: route when observable purpose, scope, invariant, interface, or
  validation truth changed.
- **ADR**: route when the diff introduces or reverses a lasting decision and the
  decision rationale is available.
- **Architecture/reference docs**: route when explanation, topology, lookup
  facts, or public reference material became stale.
- **AGENTS.md**: route when agent navigation, repository ownership, or a
  non-obvious gotcha changed.
- **Skill**: route when a repeatable, agent-executable procedure changed.
- **No update**: route when durable context remains accurate or the diff is
  mechanical, generated, release-only, or too ambiguous to justify a write.

File categories are inspection leads. Require supporting diff evidence before
choosing an owner.

For a combined historical bootstrap diff, keep owner boundaries explicit:

- `context-contracts` applies and validates SPEC/ADR contracts.
- `context-docs` applies architecture, reference, project-evolution, and index
  updates.
- `context-backfill` contributes evidence and proposals, not generated files.
- `context-review` checks the combined diff for gaps, duplication, provenance
  loss, and owner drift; it does not become another generator.

Group owners that share the same no-update evidence. Keep each route to one
evidence sentence and one usefulness sentence when possible; never shorten the
raw changed-path inventory.

## Report shape

```markdown
# Context review

Range: <base>...<head>
Repository write: no

## Raw changed paths
- <status> <old path> -> <new path>

## Evidence-backed routes
- <owner or no update>
  - Evidence: <path and hunk or exact change>
  - Reason: <durable truth affected>
  - Authority: advisory

## Deterministic errors
- None | <exact Git or parser error>

## Limitations
<Missing evidence or unavailable optional enrichment.>
```
