---
name: context-backfill
description: "This skill reconstructs proposal-only historical evidence, correctness-envelope SPEC content, ADR candidates, and architecture/evolution leads from current files, local Git history, and optional merged pull request evidence. Use when a repository or module needs a complete-picture genesis-through-cutoff backfill, or when the user explicitly requests a quick current-state reconstruction."
---

## Portable deterministic evidence

The independently installed `context-engineering` CLI and `uv` are required dependencies. From a source checkout, install it with `uv tool install ./packages/context-engineering`; then run `context-engineering ...`. If `uv` or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Context Backfill

Use this skill to produce an auditable, proposal-only reconstruction of a
repository or module at a fixed cutoff. Local Git is sufficient; merged pull
requests add optional rationale evidence.

## Activation and depth

Use **complete-picture** by default for a genesis-through-cutoff reconstruction.
For a module, begin at its first evidenced commit. Inspect in-scope phases,
renamed or deleted design artifacts, relevant diffs, and optional merged-PR
records.

Use **quick** only when the request explicitly asks for a bounded or
current-state reconstruction. Inspect the cutoff tree and a limited relevant
commit set; propose only facts and decisions needed for current contracts.

## Workflow

1. Read applicable `AGENTS.md` files. Fix an exact commit cutoff and record the
   reconstruction date. Use a detached disposable worktree when replaying a
   historical repository.
2. Confirm the pre-state and existing ADR directory convention. Do not inspect
   files or commits after the cutoff in a blinded replay.
3. Extract complete-picture local evidence by default:

   ```bash
   SKILL_DIR="<absolute path to this skill>"
   context-engineering backfill <target> \
     --cutoff <sha> --json
   ```

   The CLI must report `evidence_boundary.completeness: complete`. Stop without
   proposing SPEC, ADR, or docs content when history is shallow, module lineage
   is ambiguous, Git evidence is malformed, or a resource ceiling is reached.
   Use `resource_counts` and `limitations` in the report; never silently switch
   to quick mode.

   For an explicitly requested quick reconstruction:

   ```bash
   context-engineering backfill <target> \
     --cutoff <sha> --quick --json
   ```

4. Treat the CLI result as deterministic extraction evidence, not a finished
   backfill report. Empty claim, timeline, decision, SPEC, ADR, and docs buckets
   are intentional: the agent owns semantic synthesis in steps 4-7. Read the
   cutoff tree, relevant tests, and the diffs behind high-signal commits. By
   default, also trace the first evidenced phase, rename/delete records, and
   superseded design paths through the cutoff. Inspect nonstandard design roots
   such as `agent_docs/` and `design_docs/`, plus exact design or specification
   paths linked from applicable `AGENTS.md` or `CLAUDE.md` files; advisory
   design-artifact labels are leads, not a complete semantic inventory. For a
   module target, preserve whole-directory moves by following the CLI's exact
   target path lineage; report repository genesis separately from the target's
   first evidenced commit. Stop when the CLI reports ambiguous lineage rather
   than presenting partial history as complete. When the repository has a GitHub remote and authenticated `gh` is
   available, enrich ADR rationale and counterevidence from merged pull requests
   up to the cutoff by default. Record immutable PR URLs plus base, head, or
   merge SHAs. Mark GitHub enrichment unavailable rather than weakening local
   Git proof when the remote, network, authentication, or PR evidence is
   unavailable.
   Before compressing the proposal, cluster the complete evidence into distinct
   durable design themes. Preserve independently supported themes even when
   their commits rank below more repetitive leads; inspect source boundaries,
   target-specific behavior, validation strategy, lifecycle failure behavior,
   and superseded paths when those appear in the evidence. Compression may
   deduplicate a theme, but it must not silently erase one.
5. Build the proposal with the schema in
   [backfill report](references/backfill-report.md). Treat claim-table entries,
   SPEC assertions, ADR rationale and counterevidence, and contradiction or
   supersession statements as historical claims. Also treat a conclusion that
   a candidate was not promoted as a claim about the evidence. Give every claim
   full immutable identities, source paths, an effective date or `unknown`, and
   the reconstruction date.
   Use the CLI's portable repository identity in the report; never replace it
   with an absolute local checkout path.
   Cite every historical or cutoff-behavior assertion at the point where it
   appears, including each normative SPEC statement. A section-level cutoff
   note is context, not provenance: each assertion must name a stable evidence
   ID that resolves to a full SHA and exact repository-relative paths. Do not
   use wildcard, directory-family, or prose path summaries as if they were the
   complete raw inventory; either list every exact path/status tuple or point
   to the corresponding immutable evidence records. The raw evidence must stay
   inspectable in the delivered report or an attached immutable artifact; counts
   and assertions that an inventory exists are not evidence. A run-boundary
   record without paths cannot support a historical claim or rejection reason.
6. Draft the canonical correctness-envelope SPEC for behavior visible at the
   cutoff. Use exactly these six second-level sections, in order, with no
   additional SPEC section: `Summary`, `Goals / Non-Goals`, `Requirements`,
   `Interfaces & Contracts`, `Invariants`, and `Acceptance`. Keep unresolved
   items inside the applicable canonical section. Propose a retrospective ADR only when evidence shows both a lasting
   decision and its rationale. The absence of an existing ADR directory
   convention affects application placement, not candidate promotion; do not
   suppress an evidence-backed candidate for that reason. Record competing
   evidence and rejected candidates; never turn a commit subject, confidence
   label, or high-signal classification into rationale by itself.
7. By default, explicitly route proposed SPEC/ADR application to
   `context-contracts`. Propose architecture and project-evolution material as
   input to `context-docs`. Do not generate those documents here.
8. Report `Repository write: no`. Patch no repository file by default.
   Before sharing evidence outside the local review boundary, rerun with
   `--publish-safe`. That response omits raw subjects and historical paths,
   retains immutable commit leads, and reports sensitivity flags. Historical
   text may enter durable docs only after explicit approval.
9. Apply only after an explicit apply instruction. Re-read current truth before writing. Preserve the existing ADR convention
   when one exists; otherwise let `context-contracts` select and validate one
   explicit convention rather than deferring supported ADRs. Route architecture/reference/evolution docs and their
   indexes to `context-docs`, then use `context-review` on the combined diff.
   Never create placeholder ADRs or a decision ledger.

## Evidence rules

- Cite the exact SHA and affected path for local Git evidence.
- Cite the PR URL plus immutable base, head, or merge SHA for PR evidence.
- Use `unknown` when no effective date or rationale can be established.
- Keep contradictory claims side by side; do not silently pick one.
- Label model synthesis as inference even when it is plausible.
- Keep confidence advisory. It cannot promote an ADR, suppress evidence,
  authorize a write, or become persisted repository truth.
- Report GitHub evidence as optional, its availability as
  `available | unavailable | unknown`, and whether it was used.

## Dependencies

Require Git, `uv`, and the installed `context-engineering` command. Run `context-engineering ...`. If that command cannot run, stop and report the missing dependency; do not replace deterministic extraction with manual local-Git inspection. GitHub CLI, network access, and Harness Kit remain optional enrichment.

## Report

In quick mode, return the existing cutoff, reconstruction date,
pre-state, sources, claim table, proposed SPEC, ADR candidates,
contradictions, limitations, and write status. By default, use every section in
[backfill report](references/backfill-report.md).
