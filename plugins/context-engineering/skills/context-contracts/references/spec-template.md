# Correctness-envelope SPEC.md template

Use current, verifiable statements. Keep all six sections in this order. Delete
prompts and optional empty subsections, but never delete a required section.
Do not accept Purpose/Scope/Interfaces/Validation as aliases.

````markdown
# <Module> specification

## Summary

<What the module does, for whom, and at what boundary.>

## Goals / Non-Goals

- Goal: <observable outcome the module owns.>
- Non-goal: <adjacent behavior it does not own.>

## Requirements

- <The system MUST preserve a required behavior.>
- <The system SHOULD prefer a non-breaking default.>
- <A caller MAY choose a supported option.>

## Interfaces & Contracts

- `<entry point>` — <inputs, outputs, errors, and boundary behavior.>

## Invariants

- <Condition that must remain true.>

## Acceptance

- <Observable proof or verified test that establishes the envelope.>
````

Use MUST, SHOULD, and MAY as defined by their ordinary normative meanings; do
not use them as emphasis. Do not add roadmap items, implementation tours,
architecture narrative, or historical rationale. Route those to planning
evidence, architecture/reference/evolution docs, or ADRs.

Omit YAML indexing frontmatter unless the repository already uses it for the
same class of contract document. When it does, preserve that schema rather than
inventing a plugin-specific one.
