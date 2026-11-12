# Architecture Review Process

Forked from the `improve-codebase-architecture` skill. Preserve this process for the architecture-lens pass of an architecture polish review.

## Purpose

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point — don't drift into "component," "service," "API," or "boundary." Full definitions live in `architecture-language.md`.

- **Module** — anything with an interface and an implementation: function, class, package, or slice.
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** — the code inside.
- **Depth** — leverage at the interface: a lot of behavior behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behavior can be altered without editing in place. Use this, not "boundary."
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers get from depth.
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles:

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

## Explore

Read the relevant repo context first: AGENTS.md/CLAUDE.md files, architecture docs, module docs, and any decision records in the affected area. Do not require a `CONTEXT.md` file.

Walk the codebase organically and note where understanding creates friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they are called, with poor **locality**?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?
- Where is lifecycle ownership unclear or split across adapters and workflow/domain modules?
- Where does a caller need to know too much ordering, state, config, or error-mode detail to use a module safely?

Apply the **deletion test** to anything that looks shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" answer is the signal.

## Present deepening opportunities

For each candidate, include:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture causes friction
- **Solution** — plain-English description of what would change
- **Benefits** — explain in terms of locality and leverage, and how tests improve
- **Deletion test** — what complexity would reappear across callers if the module disappeared

Use the repository's domain language when available, and use `architecture-language.md` vocabulary for architecture. If an existing architecture decision forbids a suggested path, surface the conflict only when the friction is real enough to revisit the decision.

## Output shape

```md
## Architecture Deepening Opportunities

1. **<candidate title>**
   - Files: `path/a`, `path/b`
   - Module/interface/seam involved:
   - Problem:
   - Solution:
   - Benefits:
     - Locality:
     - Leverage:
     - Test impact:
   - Deletion test:
```

Do not propose speculative generalized frameworks unless at least two concrete adapters or use cases already exist. One adapter means a hypothetical seam; two adapters means a real seam.
