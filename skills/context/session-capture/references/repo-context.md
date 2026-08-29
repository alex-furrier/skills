# Repo-context destination

Load this reference only after a session-capture proposal targets repo context.
The main skill still owns proposal quality and explicit approval. This
reference owns repo-specific placement constraints.

## Inspect before proposing

1. Resolve the target repository and read its instructions.
2. Search existing root and nested `AGENTS.md`, ADRs, and `docs/`.
3. Dedup against the likely owner; prefer an update over a parallel artifact.
4. Check whether the knowledge applies repo-wide or only beneath one module.

## Placement

- Put cross-cutting invariants in the root `AGENTS.md`.
- Put module-specific behavior in the nearest applicable nested `AGENTS.md`.
- Keep AGENTS guidance lean and use `DO / NOT / BECAUSE` when it expresses a
  repeatable gotcha.
- Treat 250 lines as the normal AGENTS capacity target. When the addition would
  exceed capacity or needs explanatory depth, route it to an existing or new
  `docs/` owner and add only a concise pointer when useful.
- Prefer an existing ADR or document when it already owns the decision.
- A repeatable procedural workflow may belong in an existing skill rather than
  repo prose; revise the proposal if inspection establishes that owner.

Root versus nested placement is based on applicability, not the path mentioned
most often in the transcript.

## Attribution

Content materially derived from session history should carry:

```markdown
<!-- source: session-history | session: <session-id> | extracted: YYYY-MM-DD -->
```

For a new document with YAML frontmatter, place the comment after the closing
frontmatter delimiter. Do not tag facts independently established from current
code or authoritative repo documentation.

## Apply after approval

- Follow the repository's edit, test, review, and publication workflow.
- Name every required documentation index in the proposal before approval and
  give it a selectable companion identifier distinct from the primary write.
  Creating a document does not implicitly authorize its index update. If an
  index requirement is discovered only while applying an approved capture,
  stop and issue a revised proposal that names the companion target.
- Preserve the approved scope; do not expand one capture into a general docs
  rewrite.
- Report line-count/capacity impact for AGENTS changes.
- If dedup during implementation proves the learning is already complete,
  make no duplicate write and report the existing canonical owner.
