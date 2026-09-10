# Generated AGENTS.md Specification

Use this reference while writing an AGENTS.md. The canonical section order,
tier rules, and inclusion decisions belong to the owning
[`context-agents-md` SKILL](../SKILL.md); do not restate them here.

## Watermark

AGENTS.md files are routing indexes and do not use YAML frontmatter. Append
this HTML comment as the final line, using the current release and date:

```markdown
<!-- generated-by: context-engineering@X.Y.Z | last-updated: YYYY-MM-DD -->
```

The watermark is invisible to readers and supports adoption and staleness
checks.

## Validate before inclusion

Include only claims confirmed from the target repository or supplied evidence.
Before documenting a command, confirm that it exists in the relevant manifest,
configuration, CI workflow, or source. When it is safe and feasible, perform a
non-destructive check such as `--help`, target listing, or dry run.

Do not document volatile counts, timings, or generated output. In interactive
mode, surface plausible but unvalidated candidates for review. In auto mode,
omit them. Preserve the owner's portability, safety, and environment-specific
dependency rules when a validated command needs them.

## Related owners

- `context-agents-md` owns generated AGENTS.md structure, CLAUDE.md handling,
  and candidate selection.
- `context-docs` owns documentation trees, indexes, explanations, and reference
  pages. Link to an existing docs tree when useful; do not create or reorganize
  it from this workflow.
- `session-capture` owns later user-approved capture of durable corrections.
