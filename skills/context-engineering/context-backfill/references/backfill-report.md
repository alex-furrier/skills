# Backfill proposal schema

Use this shape as a reporting guide, not a machine authority.

## Contents

- Run identity
- Evidence IDs and claims
- Complete-picture sections
- Proposed SPEC
- Retrospective ADR candidates
- Proposed context-docs material
- Confidence boundary

## Run identity

- Repository and module
- Portable repository identity from the CLI; never serialize an absolute checkout path
- Cutoff SHA
- Repository genesis SHA
- Target first evidenced commit and target path lineage (for a module target)
- Reconstruction date
- GitHub evidence: optional
- GitHub availability: available | unavailable | unknown
- GitHub used: yes | no
- Repository write: no or yes
- Mode: quick | complete-picture
- Evidence completeness: complete | bounded | incomplete | unknown
- Resource counts: records, paths, bytes, subprocesses
- Publication mode: local-evidence | publish-safe
- Sensitivity flags and publish-safe omissions

Do not synthesize proposals when completeness is `incomplete` or `unknown`.
Before an external handoff, use publish-safe rendering or obtain explicit
approval for the named historical text and paths.

## Evidence IDs and claims

Record each claim independently. "Claim" includes proposed SPEC assertions,
ADR rationale and counterevidence, contradiction or supersession statements,
and reasons for not promoting a candidate—not only rows in the primary claim
table.

```yaml
kind: verified_fact | inference | contradiction
claim: <bounded statement>
effective_date: YYYY-MM-DD | unknown
reconstruction_date: YYYY-MM-DD
provenance:
  - source: local-git | merged-pr | cutoff-tree
    commit: <immutable SHA>
    paths: [<repo-relative path>]
    url: <optional immutable PR URL>
```

For a contradiction, cite every conflicting source. Never replace the evidence
with a single resolved label.

Use stable evidence IDs for repeated sources. The ID must resolve to full
immutable identities, paths, status, and date. A claim may cite that ID instead
of repeating the provenance block.

Attach one or more of those IDs directly to every assertion wherever the
assertion appears. This includes each proposed SPEC bullet, ADR statement,
timeline phase, contradiction, and rejection reason. A shared cutoff or source
header does not satisfy claim-level provenance. Never use wildcards or prose
path groups as substitutes for exact path/status records in the raw inventory;
when the inventory is too large to inline, reference the immutable evidence
artifact or exact evidence IDs that contain all tuples. The referenced artifact
must be delivered with the report and bound by a SHA-256 digest; an unmaterialized
claim that a full inventory exists is insufficient. A run-boundary record with
no paths establishes execution metadata only and cannot prove a historical
change, candidate rejection, or design conclusion.

## Complete-picture sections

Complete-picture reports keep these sections separate:

1. **Raw evidence** — the full repository genesis-through-cutoff inventory, or
   exact module-lineage inventory from the target's first evidenced commit
   through cutoff. Include rename/delete status and historical paths. Report
   repository genesis separately for a module; never pad module evidence with
   an unrelated genesis record. High-signal labels are advisory leads beside
   the raw inventory; they never replace it. Stop on ambiguous module lineage.
2. **Verified facts** — bounded statements directly established by evidence.
3. **Inference** — model synthesis that remains labeled and revisable.
4. **Contradictions and supersession** — all conflicting sources, effective
   ordering when verified, and unresolved conflict when ordering is unknown.
5. **Phase timeline** — the first evidenced phase through cutoff, with each
   phase citing immutable evidence.
6. **Decision inventory** — all lasting-decision leads, including promotion and
   rejection disposition.
7. **ADR promotion suggestions** — decision, evidenced rationale, lasting
   relevance, counterevidence, effective date, and provenance.
8. **Rejected candidates** — candidate, cited rejection reason, and evidence
   gap when rationale is unavailable.
9. **Evidence gaps** — missing rationale, unavailable PR data, ambiguous dates,
   and cutoff limitations.
10. **Proposed correctness-envelope SPEC** — current cutoff behavior only.
11. **Proposed context-docs material** — separate architecture and project-
    evolution outlines with provenance.

Before ranking or deduplicating leads, check the complete evidence for distinct
durable design themes. Retain independent evidence for each theme even when it
is less frequent than repetitive implementation activity. In particular,
inspect interface and target-specific boundaries, validation strategy,
lifecycle/error policy, source-of-truth ownership, and superseded design paths
when present; these are evidence categories to inspect, not required decisions
to invent.

## Proposed SPEC

Draft exactly these six second-level sections in this order: Summary; Goals /
Non-Goals; Requirements; Interfaces & Contracts; Invariants; and Acceptance.
Do not split `Goals / Non-Goals`, rename `Interfaces & Contracts`, or add an
unresolved-items section; keep unresolved items inside the applicable canonical
section. Requirements use MUST, SHOULD, or MAY. Put a clearly scoped cutoff
SHA or stable evidence ID, exact source paths, effective date, and
reconstruction date on each assertion. A shared header may supply common dates
for a group, but it cannot replace claim-level evidence IDs and exact paths.
Mark unresolved statements instead of completing the shape with guesses.

Route proposed SPEC and ADR application to `context-contracts` in the report.

## Retrospective ADR candidates

For each candidate, name the decision, evidence of rationale, effective date,
counterevidence, and why the decision remains architecturally relevant. Attach
full SHAs and paths to the rationale and counterevidence. Return `None` when
evidence establishes only that a change happened.

## Proposed context-docs material

Provide two independent outlines when evidence supports them:

- **Architecture** explains current structure, responsibility boundaries, and
  call/data flow at the cutoff.
- **Project evolution** explains evidenced phases, supersession, and retained
  tradeoffs over time.

Route these proposals to `context-docs`. Do not generate files, indexes, or
frontmatter here. Suggest YAML indexing frontmatter only when evidence from the
independently governed target `docs/` tree establishes that convention.

## Confidence boundary

Confidence may help a reviewer prioritize verification. It cannot promote an
ADR, suppress evidence, authorize a write, or become persisted truth. Promotion
requires the evidence tests above regardless of confidence.
