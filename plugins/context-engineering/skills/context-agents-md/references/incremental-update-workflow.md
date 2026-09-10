# Incremental Update Workflow

Update only the context affected by evidence. A full scan is an exception, not
the default.

## Orientation

Start by reading the existing AGENTS.md and the relevant portions of the
owning `context-agents-md` skill. Preserve accurate content, the source
identity of session-derived material, safety warnings, and the final watermark.
The canonical output shape and section rules remain with that owner.

## How to Work Here

When the contributor tier permits workflow guidance, use this optional section
to describe an evidenced sequence. Do not add it merely to narrate a command.
If the tier does not permit it, omit it and route any useful candidate through
the owner's review handling.

## Commands

Run the staleness assessment:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering staleness <path-to-AGENTS.md> --json
```

Read every changed path and its classification reason. The impact labels and
recommendation are advisory navigation aids, not decisions. Record any
classification or recommendation that you override and why.

After an approved update, run the owner-required checks:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering references <target>
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering antipatterns <target>
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering depth <target>/AGENTS.md
```

When the update also changes a governed docs tree, run:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering frontmatter <target>
```

Fix failures in files changed by this update; report pre-existing failures
without silently broadening the work.

## Gotchas

- Do not treat a `full-rebuild` recommendation as a force condition. First
  confirm a malformed AGENTS.md, widespread broken references, significant
  repository reorganization, or an explicit user request.
- Inspect changed paths before changing a section. A high-impact label does not
  establish that the documented behavior changed.
- Preserve accurate sections rather than rewriting them for uniformity.
- Keep audit and apply separate. A proposed change needs the applicable user
  approval before it is written.

## Related Context

- See the `context-agents-md` SKILL for canonical output, tier, provenance, and
  relocation rules.
- See `generated-doc-spec.md` for watermark and inclusion-validation details.
- Use `session-capture` only for later user-approved durable correction capture.
