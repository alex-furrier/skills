# Repository writing sweep

Use agent judgment to find and classify authored prose. Keep the checker source-bound and read-only for every candidate; repository update mode applies edits outside the checker.

## Choose the mode

- **Repository audit:** Discover, check, and report without editing. Use this mode when the request asks to inspect, audit, or run writing-check across a repository without explicitly requesting updates.
- **Repository update:** Require an explicit request to update or fix repository writing. Proceed without per-file confirmation, but make conservative edits rather than wholesale rewrites.

Treat “full auto” as operationally unattended execution of justified updates. Do not treat it as permission to rewrite every document or accept every finding.

## Discover the corpus

1. Read repository and nested guidance before selecting files.
2. Start from every unique tracked human-readable documentation source, not a hand-picked likely subset. With Git, enumerate tracked Markdown, MDX, reStructuredText, and authored documentation text files; without Git, enumerate the equivalent repository tree. Include root docs, documentation directories, READMEs, AGENTS/CLAUDE guidance, contributing and release docs, specifications, ADRs, architecture or design roots, and other durable context.
3. Resolve symlinks and demonstrated compatibility aliases to one prose-check candidate, but keep every alias as a path-level ledger entry. Validate relative links, scoped guidance, and ownership claims from each alias path even when Vale runs once on the owning source. Keep independently owned paths as separate candidates even when their bytes happen to match.
4. Build a pre-check corpus ledger containing every discovered source and its disposition: check, duplicate alias, generated, dependency, archive, fixture, vendored/copied, or unresolved provenance. Do not omit a discovered source silently.
5. Exclude dependencies, generated output, archives, fixtures, vendored material, and copied third-party documentation unless the request includes them.
6. Record every checked file with its selected profile. Record every exclusion and the reason for it.
7. Resolve uncertain ownership or provenance before checking or editing; do not guess that generated or vendored prose is author-owned.

Choose profiles from document purpose rather than file extension alone:

| Document purpose | Profile |
| --- | --- |
| Repository or module README | `readme` |
| Release, contributing, operational, AGENTS, and other reference documentation | `technical-doc-reference` |
| Architecture, rationale, explanation, and conceptual documentation | `technical-doc-explanatory` |

Use another existing profile when the destination clearly owns it. State ambiguous profile choices in the report instead of inventing a new profile or changing checker policy.

## Check each candidate

1. Inspect meaning and structure against current repository truth. Verify links to repository files, documented command surfaces, source-of-truth claims, and ownership boundaries with safe local evidence.
2. Apply [the contextual style review](style-review.md) within each document and across comparable titles or summaries when readers encounter them together. In update mode, make justified initial revisions through the destination owner before diagnostics; audit mode reports without edits. Do not impose one template across different purposes.
3. Inspect the checker help once. After discovery has produced explicit exact source/profile pairs, either run `writing-check` per candidate or use the bounded caller-side path: `writing-check-sweep --candidates pairs.json --jsonl`, where `pairs.json` is a non-empty JSON array of objects containing exactly `source` and `profile`. It performs no discovery and accepts no stdin candidate.
4. Retain each schema-v3 JSON Lines record independently. The caller validates the bundled policy for each candidate and shares only the in-process Vale version probe; source bytes, policy digest, findings, readability state, raw tool evidence, and status remain candidate-specific.
5. Keep semantic and style judgments separate from CLI records. Do not combine them into a score, quality verdict, readiness gate, or new aggregate schema. A clean checker result cannot establish documentation health.
6. Treat unavailable or execution-error records as missing evidence, not clean results.
7. Keep dispositions bound to the exact `source.sha256`. After any diagnostic-driven edit, recheck meaning and contextual style, discard stale records, and rerun the CLI on the changed candidate. Keep justified residual findings rather than undoing useful prose to satisfy them.

## Apply repository updates

In repository update mode:

1. Verify findings against repository truth and document purpose before editing.
2. Preserve factual behavior, qualifications, and safety, authentication, authority, privacy, security, billing, legal, and contractual constraints. Honor literal requirements for policy and license integrity, machine-consumed syntax, machine-managed blocks, and explicitly owner-marked text. Historical status alone does not protect other prose from revision.
3. Prefer coherent section rewrites over conservative sentence patching when structure or readability is poor. Compress or remove obsolete implementation detail when the destination owner no longer needs it, especially in long retrospective ADRs and superseded plans.
4. Route specialized documents to their existing owners when material structure or meaning changes: use `readme-improver` for READMEs, `context-agents-md` for AGENTS files, `context-contracts` for specifications and ADRs, and `context-docs` for structured architecture or reference documentation. Use `writing-core` for ordinary technical prose.
5. If a required destination owner is unavailable, limit edits to clearly semantics-preserving corrections and defer structural or meaning-sensitive findings with a reason.
6. Validate documented commands and factual claims with safe repository evidence. Do not run host-mutating or external-service-mutating examples merely to validate prose.
7. Rerun writing-check on every changed exact candidate and disposition the fresh findings.

### Run a bounded rewrite loop

Use one shared budget of no more than three rewrite passes after the initial check. Stop when no justified edits remain, even if Vale findings or readability shortfalls remain. `no_findings` and normal-sample FRE 55 / FK 10 are advisory observations, not acceptance criteria:

1. Revisit meaning, structure, and contextual style before choosing which diagnostic findings to act on. Rewrite coherently when useful rather than applying a sequence of local substitutions.
2. Use a `normal` sample's readability shortfall to locate dense prose. Improve ordering, sentence length, paragraph size, or list structure only when it helps the reader and preserves the intended content.
3. On every pass, recheck contextual style and the destination owner's technical and authority constraints from step 2, including ADR decisions and executable commands.
4. Rerun writing-check on the exact rewritten candidate after each pass and discard every stale record and disposition. Stop early when no justified revisions remain; retained observations need a specific reason, not another blind rewrite pass.
5. Never apply a blind punctuation or substitution sweep. Splitting a sentence must produce two grammatical, correctly capitalized sentences; changing dashes, colons, contractions, or passive voice must preserve the surrounding meaning. Do not chase `no_findings` by changing exact terms, required text, quotes, deliberate voice, or known false positives. Do not game either formula or expand familiar technical terms merely to change a score.
6. After the third pass, separate actionable findings from justified required-text residuals. Disposition each residual against the final source with one concrete category and reason. Do not bulk-disposition a large queue with a generic fidelity claim when coherent compression or rewriting can still remove it. Report unmet normal-sample metrics, attempted improvements, and the specific precision or authority boundary that blocks further rewriting.

Run the finding-resolution portion for `insufficient_sample`, `small_sample`, and `composition_limited` results, but do not assign them a readability target. Do not rewrite for `disabled`, `unavailable`, or `execution_error`; report the unusable checker state instead. The bounded loop is workflow guidance, not a checker gate or a new exit condition.

Do not add repository discovery, network access, or auto-fix behavior to `writing-check`. The separate bounded caller emits only independent JSON Lines records, not an aggregate schema.

## Report

Report:

- the complete discovered corpus ledger, including checked files, duplicate aliases, and every exclusion;
- checked files and selected profiles;
- skipped files and reasons;
- fixed, kept, and deferred findings per exact candidate;
- unavailable or failed checks;
- commands and claims validated, including anything not run;
- changed files and destination owners used in update mode.

Keep the report descriptive. Findings and counts do not establish writing quality or repository readiness.
