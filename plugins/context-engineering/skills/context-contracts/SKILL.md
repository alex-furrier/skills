---
name: context-contracts
description: "This skill analyzes, validates, bootstraps, migrates, and updates correctness-envelope SPEC.md and ADR contracts from current repository truth. Use when a repository or module needs a current specification, decision records, contract validation, legacy SPEC migration, or a context contract refresh."
---

## Portable deterministic evidence

The independently installed `context-engineering` CLI is required. If missing, request explicit install consent. With `uv` and authenticated `gh` access to the private `alex-furrier/skills` repository, clone to a directory you control, inspect and trust the checkout, then run `uv tool install "$checkout/skills/packages/context-engineering"` and `context-engineering --help` (set `checkout="$(mktemp -d)"`; run `gh repo clone alex-furrier/skills "$checkout/skills"`). From an existing trusted checkout, `uv tool install ./packages/context-engineering` works. If `uv`, `gh`, access, network, install, or help fails, stop and report deterministic analysis unavailable; never install automatically or substitute manual inspection.

# Context Contracts

Use this skill when current repository behavior needs a small, factual, portable
SPEC or ADR record. It works from current truth; use `context-backfill` for
historical reconstruction.

## Activation and workflow

1. Read applicable `AGENTS.md` files and identify the repository or module root.
2. Discover current conventions before proposing files:

   ```bash
   SKILL_DIR="<absolute path to this skill>"
   context-engineering contracts <target> --json
   ```

   Add `--require-spec` or `--require-adrs` only when repository policy or the
   request explicitly requires that artifact. Absence is otherwise valid.
   Discovery is recursive: existing nested SPEC files, `adr/`, `adrs/`,
   `decisions/`, and architecture decision trees take precedence over bundled
   templates.
3. Read current code, tests, public interfaces, configuration, and existing
   architecture/reference docs. Use Git history only to explain current truth;
   route historical reconstruction to `context-backfill`.
4. Select one mode:
   - **Analyze** reports current contracts, conventions, gaps, and contradictions.
   - **Validate** returns deterministic findings without editing files.
   - **Bootstrap** drafts one correctness-envelope `SPEC.md` and an ADR only
     when a lasting decision has evidence.
   - **Migrate** replaces the retired Purpose/Scope/Interfaces/Validation
     profile with the canonical profile; never retain both as aliases.
   - **Update** proposes the smallest edits that match current repository truth.
5. Present a file-by-file proposal and report `Repository write: no`.
6. Write only after an explicit apply instruction. Preserve every existing ADR
   directory and filename convention. Never create a placeholder ADR, empty ADR
   directory, or separate decision ledger.
7. Re-run `contracts` after apply, then run `context-engineering check` against
   the intended base/head range. Fix deterministic errors before handoff;
   evaluate semantic routes separately with `context-review`.

Use [SPEC template](references/spec-template.md) and
[ADR template](references/adr-template.md) when creating an artifact. Keep the
six required SPEC sections in their canonical order. State obligations under
Requirements with MUST, SHOULD, or MAY. Mark a value `Unknown` with the evidence
gap and date when it cannot be verified. Omit only optional prose rather than
guessing or replacing missing facts with plans.

Add YAML indexing frontmatter only when the target already establishes that
convention. Preserve the established schema. A repository with no indexing
frontmatter convention receives plain Markdown.

## Contract boundaries

- Let `SPEC.md` state current summary, goals/non-goals, normative requirements,
  interfaces/contracts, invariants, and acceptance evidence.
- Let ADRs record lasting decisions and their known rationale, not every change.
- Keep architecture/reference docs responsible for explanation and lookup.
- Keep `AGENTS.md` responsible for agent routing and non-obvious gotchas.
- Keep skills responsible for repeatable procedures.

## Dependencies

Require Git, `uv`, and the installed `context-engineering` command. Run `context-engineering ...`. If that command cannot run, stop and report the missing dependency; do not replace deterministic validation with manual discovery.

## Report

Return the mode, target, discovered convention, deterministic findings,
proposed files or edits, evidence paths, validation command, and whether a
repository write occurred.
