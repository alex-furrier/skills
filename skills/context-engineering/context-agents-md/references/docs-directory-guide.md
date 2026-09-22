# docs/ Directory Guide

`docs/` is optional depth beyond a lean AGENTS.md. `context-agents-md` may link
an existing docs tree, but `context-docs` owns docs analysis, content,
placement, and indexes.

## Bootstrap shape

For a new unmanaged tree, generate only the content the module needs:

```text
docs/
  README.md
  AGENTS.md
  explanation/
    architecture.md
  reference/
    cli.md
```

- Use `explanation/` for current system design, boundaries, and evolution.
- Use `reference/` for commands, APIs, schemas, outputs, and durable data.
- Prefer a topic name such as `cli.md` or `interfaces.md` over a universal
  filename.
- Create no empty folders.
- Route repeatable procedures to skills rather than `docs/how-to/`.
- Route onboarding walkthroughs to the repository README or its established
  onboarding surface rather than generating `docs/tutorials/`.

## Existing docs trees

Repository conventions take precedence over this bootstrap shape.

- Preserve established tutorial, how-to, framework, and flat layouts.
- Do not reorganize MkDocs, Docusaurus, Sphinx, or mdBook content around this
  plugin's taxonomy.
- Preserve existing YAML frontmatter only when that independently governed docs
  tree establishes it. Do not introduce frontmatter to a plain-Markdown tree.
- Add or update docs only through `context-docs` with explicit write authority.

## Indexes

An unmanaged tree created by `context-docs` gets:

- `docs/README.md` for human reading order, with explanation before reference;
- `docs/AGENTS.md` for agent routing by document type, without YAML
  frontmatter.

Both indexes cover every governed docs file. Existing framework navigation may
remain authoritative instead of a generated README when moving it would
conflict with the framework.

## Content routing

| Content | Owner or destination |
|---|---|
| System design, boundaries, data flow | `docs/explanation/<topic>.md` |
| Commands, APIs, schemas, outputs | `docs/reference/<topic>.md` |
| File maps, module commands, gotchas | nearest `AGENTS.md` |
| Repeatable agent procedure | `.agents/skills/<name>/SKILL.md` proposal |
| Onboarding walkthrough | repository README or established onboarding surface |
| Temporary migration state | plan or task system |
| Unverifiable content | preserve at source and report the evidence gap |

## Referencing from AGENTS.md

Keep the root pointer concise because `docs/AGENTS.md` owns detailed routing:

```markdown
## Related Context

| Path | Topic |
|---|---|
| `docs/` | Architecture and reference material |
```

## Validation

Run the shared validators from the target module:

```bash
context-engineering references .
context-engineering frontmatter .
```

For PR or full-tree proof, use `context-engineering check` so nested context
roots are validated against exact Git trees.
