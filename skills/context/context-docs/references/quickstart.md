# Docs quickstart generator

Use this reference for `context-docs` quickstart mode. Generate a compact,
durable documentation tree for a concrete repository or module. Keep
procedures in skills and onboarding in the repository README; generated
`docs/` content is explanation and reference only.

## Contents

- [Inputs](#inputs)
- [Placement](#placement)
- [Architecture](#architecture)
- [Project evolution](#project-evolution)
- [Interfaces and command reference](#interfaces-and-command-reference)
- [Indexes](#indexes)
- [Historical intake](#historical-intake)
- [Final checks](#final-checks)

## Inputs

- `feature_dir`: repository-relative target path.
- `scope`: modules and behavior covered.
- `known_docs`: existing related documentation, when present.
- `historical_proposal`: optional complete-picture `context-backfill` report.

Infer these from current source, tests, configuration, and the approved
backfill proposal. Omit unsupported content rather than completing a template
with guesses.

## Placement

Write under `<feature_dir>/docs/`. Never write to the repository root docs tree
unless the target is the repository root.

For a new unmanaged docs tree, use:

```text
docs/
  README.md
  AGENTS.md
  explanation/
    architecture.md
    project-evolution.md   # only when historical evidence supports it
  reference/
    interfaces.md
    data.md                # only when meaningful persistent data exists
```

Create only folders with content. Do not generate `tutorials/` or `how-to/`.
Repeatable agent-executable procedures belong in skills. Keep onboarding in
the repository README.

When a documentation framework owns the target tree, preserve its structure
and navigation file. Do not create `docs/README.md` for a framework-managed
tree; do create `docs/AGENTS.md` as an agent routing index.

## Architecture

`docs/explanation/architecture.md` explains current structure and ownership:

- responsibility boundaries;
- entry points and important call or evidence flow;
- deterministic versus semantic authority;
- external dependencies and failure boundaries;
- links to SPEC, ADRs, and precise reference material.

Prefer one small Mermaid `flowchart LR` when it materially improves the
explanation. Keep diagrams under ten nodes, use short labels, and avoid
parentheses in node text. Do not add a diagram merely to decorate the page.

## Project evolution

Create `docs/explanation/project-evolution.md` only from a complete historical
proposal. Describe evidenced phases, supersession, and retained tradeoffs.
Attach immutable commit and path provenance to each historical assertion.
Keep lasting decisions and rationale in ADRs; use project evolution for the
broader sequence that does not qualify as a decision record.

## Interfaces and command reference

Create a topic-named page under `docs/reference/` as a lookup surface for
current public commands, APIs, schemas, output fields, exit behavior, and
dependencies. Use `docs/reference/cli.md` for command-driven modules and
`docs/reference/interfaces.md` for API- or schema-driven modules. Prefer an
existing repository naming convention. Use tables and small examples, and
verify commands from the actual CLI or source.

Create `docs/reference/data.md` only when the module has meaningful persistent
data, cache keys, or durable state not already owned by SPEC or interface
reference material.

## Indexes

Create both indexes for an unmanaged tree:

- `docs/README.md`: human reading order, explanation before reference.
- `docs/AGENTS.md`: agent routing tables by document type, without YAML
  frontmatter.

Every governed docs file must appear in both applicable indexes. Preserve
existing frontmatter only when the independently governed target docs tree
already establishes it.

## Historical intake

Treat backfill as evidence and proposals, not generated text or write
authority:

1. Recheck current architecture claims against current source.
2. Preserve claim-level provenance for evolution material.
3. Route SPEC and ADR content to `context-contracts`.
4. Route AGENTS.md updates to `context-agents-md`.
5. Send the combined diff to `context-review`.

## Final checks

- Every statement is verified or explicitly marked unknown.
- No volatile counts are presented as durable facts.
- No workflow prose duplicates an existing skill.
- Pages remain under 300 lines.
- Internal links resolve.
- `docs/README.md` and `docs/AGENTS.md` cover the generated tree.
- `docs_verify.py`, `context-engineering references`, and
  `context-engineering antipatterns` pass or report exact pre-existing gaps.
