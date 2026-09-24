---
name: context-review
description: "This skill reviews a branch or pull request diff for missing durable context and routes evidence toward SPEC.md, ADRs, architecture/reference docs, AGENTS.md, skills, or no update. Use during PR review or before handoff when context drift may accompany code changes."
---

## Portable deterministic evidence

The independently installed `context-engineering` CLI is required. If missing, request explicit install consent. With consent and `uv`, run `uv tool install context-engineering-cli==2.6.0` (published on PyPI), then `context-engineering --help`. As an optional source fallback, with authenticated `gh` access to the private `alex-furrier/skills` repository, set `checkout="$(mktemp -d)"`, run `gh repo clone alex-furrier/skills "$checkout/skills"`, inspect and trust the checkout, then run `uv tool install "$checkout/skills/packages/context-engineering"` and `context-engineering --help`. From an existing trusted checkout, `uv tool install ./packages/context-engineering` works. If `uv`, network, install, or help fails (or `gh` or access fails on the source route), stop and report deterministic analysis unavailable; never install automatically or substitute manual inspection.

# Context Review

Use this skill before handoff or during pull-request review when a diff may have
changed durable context. It reviews ownership without writing files. The Git diff
remains the source evidence; path labels are only inspection leads.

## Workflow

1. Read applicable `AGENTS.md` files. Freeze the exact base and head SHAs; use
   the pull request's immutable identities when available.
2. Run the composed deterministic check against the exact merge-base and head
   trees:

   ```bash
   SKILL_DIR="<absolute path to this skill>"
   context-engineering check <target> \
     --base <base-sha> --head <head-sha> --json
   ```

   Contract, docs-structure, parser, and Git failures are blocking findings.
   Semantic owner routes remain advisory. Use `--all` for full-repository CI.
3. The composed `check` result already includes the semantic analyzer's raw
   changed paths, rename pairs, evidence, and `advisory_routes`; inspect those
   fields when reviewing diff hunks. Do not run a second `review` command for
   the same range.
4. Stop on exact Git errors. Otherwise inspect the retained raw changed paths,
   rename pairs, and relevant hunks. Analyzer route labels remain advisory.
5. Apply the ownership tests in [review routing](references/review-routing.md):
   route to `SPEC.md`, ADRs, architecture/reference docs, `AGENTS.md`, skills,
   or no update only when the diff evidence supports that owner.
6. Cite raw paths and hunks for every recommendation. A category, score, or
   filename pattern cannot independently fail the review, authorize a write, or
   discard evidence.
7. Group compatible no-update routes. Avoid repeating one hunk under several
   owners; keep each route to one evidence sentence and one usefulness sentence
   when that preserves the decision.
8. When reviewing a complete-picture application, evaluate the combined diff:
   `context-contracts` owns SPEC/ADR edits, while `context-docs` owns
   architecture/reference/project-evolution docs and indexes. Flag duplicated
   ownership or historical assertions that lost provenance. Do not regenerate
   either owner's output.
9. Report `Repository write: no`. Prefer no update when current context remains
   accurate.
10. Apply only after an explicit apply instruction and only when the edit is
   unambiguous from current evidence. Keep ambiguous routes as review findings;
   request a decision rather than guessing. Revalidate the affected context
   owner after any write.

## Boundaries

- Review context completeness, not general code quality.
- Treat a source-code change as an inspection lead, not proof that SPEC or ADR
  work is needed.
- Preserve both old and new paths for renames.
- Separate deterministic tool errors from semantic review judgment.
- Keep Harness Kit optional and change-local when present.
- Keep backfill confidence and semantic routes advisory; neither can suppress
  raw evidence or authorize a repository write.

## Dependencies

Require Git, `uv`, and the installed `context-engineering` command. Run `context-engineering ...`. If that command cannot run, stop and report the missing dependency; do not replace the deterministic analyzer with manual diff inspection. Harness Kit and GitHub access remain optional.

## Report

Use the report shape in [review routing](references/review-routing.md). Include
the exact range, raw changed paths, evidence-backed routes, no-update decisions,
deterministic errors, limitations, and write status.
