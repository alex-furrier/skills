---
name: repository-context-refresh
description: "This skill audits or refreshes a repository's durable context and human-readable documentation by orchestrating complete-picture history backfill, merged-PR rationale, SPEC/ADR/architecture/AGENTS owners, factual-drift inspection, source-bound writing checks, and bounded rewrites. Use when a repository needs a context sweep, documentation health pass, historical backfill, or combined context-and-docs cleanup."
---

## Portable deterministic evidence

The Context CLI and `uv` are required plugin dependencies. Install the complete Context plugin, including `cli/`; do not copy a Context skill alone. Run `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering ...`. If `uv`, the package, or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Repository Context Refresh

Use this skill for a repository-wide context or documentation sweep. It coordinates
existing owners; it does not replace their contracts or create a new workflow owner.

## Activation and mode

Use **Audit** by default for requests to review, sweep, check, or find stale
material. Audit inspects and returns a proposal without changing repository files,
Git, or GitHub.

Use **Apply** only when the request explicitly says to update, fix, apply, or
refresh files. Apply routes approved work to destination owners. The calling
operator retains worktree, branch, commit, push, and PR decisions.

## Dependencies

Require these context-engineering skills:

- `context-backfill`
- `context-contracts`
- `context-docs`
- `context-agents-md`
- `context-review`

Use `writing-check` for the documentation lane. Discover skills by intent and metadata rather than assuming a runtime prefix.

If a context owner is unavailable, stop and report the missing owner. If `writing-check` is unavailable:

- In Audit, complete the context lane, mark writing/readability evidence unavailable, and do not substitute another linter or claim a complete documentation sweep.
- In Apply, stop before the first write so the repository cannot receive a partial combined refresh.

## Workflow

### 1. Establish scope and authority

1. Read root and nested `AGENTS.md` or `CLAUDE.md` guidance.
2. Record repository identity, target module, exact cutoff SHA, current branch/worktree, dirty state, and allowed effects.
3. Let the calling operator decide whether to use the canonical checkout, a disposable cutoff worktree, or a feature worktree. Do not create branches, commits, PRs, or merges inside this skill.
4. Stop before modifying uncertain dirty work. In Audit, prefer an exact clean cutoff and keep all generated evidence outside the repository unless the operator names a durable evidence destination.
5. Treat dependency caches and environments as effects. Put uv environments outside both the target and skill source, use lock/config isolation when available, and compare status for every checkout that a command could mutate.

### 2. Build the complete context picture

Run `context-backfill` in complete-picture mode unless the user explicitly requests quick mode.

Require the context lane to:

- trace history from genesis or the target's first evidenced commit through the cutoff;
- inspect renamed, deleted, superseded, and nonstandard design paths;
- inspect current source, tests, contracts, and applicable agent guidance;
- enrich ADR rationale and counterevidence from merged pull requests when GitHub is available;
- preserve immutable Git and PR provenance;
- distinguish verified facts, inference, contradictions, and evidence gaps;
- propose SPEC, retrospective ADR, architecture, evolution, and AGENTS updates only when evidence supports them.

Treat the CLI's `github_enrichment: not-requested` as extractor scope, not the workflow result. When GitHub is available, query merged PRs with number, URL, body, merged time, base SHA, head SHA, and merge SHA; retain only PRs whose merge SHA is an ancestor of the cutoff. Save the complete filtered records and record enrichment availability and use. When unavailable, mark the gap and continue with complete local Git evidence.

Do not suppress an evidence-backed ADR because the repository lacks an existing ADR directory. Let `context-contracts` choose and validate one explicit convention during Apply.

### 3. Build the complete documentation picture

Load the `writing-check` repository-sweep workflow.

Require the documentation lane to:

- build one immutable inventory shared by both context and writing lanes;
- enumerate every tracked human-readable path before exclusions;
- distinguish `path entries` from deduplicated `owning sources` in every count;
- retain every alias as a path-level ledger entry and validate path-sensitive links and ownership;
- record generated, dependency, archive, fixture, vendored, copied, and unresolved-provenance exclusions with evidence such as symlink target, byte digest, SYNC marker, generator owner, or directory contract;
- select profiles by document purpose;
- run one source-bound checker invocation per owning source through a caller-side loop and manifest outside `writing_check.py`;
- inspect links, command surfaces, source-of-truth claims, and ownership boundaries against current repository truth;
- when executable CLI help is unavailable or would require trusting/mutating tool state, inspect parser source and command tests instead and mark CLI-help validation incomplete;
- report Vale/readability observations separately from factual or structural drift.

Never combine findings into a score or treat a clean checker result as documentation correctness.

### 4. Reconcile the audit

In Audit, return one proposal with:

1. Run identity, cutoff, evidence completeness, dependency effects, and unavailable enrichment.
2. Context findings: verified current behavior, contradictions, timeline, decision candidates, rejected candidates, and proposed owner routes.
3. Documentation corpus ledger: path-entry and owning-source counts, aliases, exclusions with provenance, profiles, checker states, and readability applicability.
4. A compact per-source table with path, profile, source digest, checker state, readability applicability/metrics, rule families, and factual drift.
5. A ranked Apply plan grouped by destination owner.
6. Validation that would be required after Apply.
7. `Repository write: no`.

For SPEC/ADR/docs proposals in Audit, default to owner-routed clauses, decision candidates, and outlines rather than final replacement files. Produce a complete transient draft only when the user explicitly requests draft candidates as report content. Never create placeholder context files.

### 5. Apply through destination owners

In Apply, freeze the approved scope before writing and execute in this order:

1. `context-contracts` applies or updates the canonical SPEC and evidence-backed ADRs.
2. `context-docs` applies architecture, reference, evolution, navigation, or consolidation updates.
3. `context-agents-md` updates lean routing and repository gotchas.
4. The destination owner for each remaining document applies factual and structural corrections.
5. After editing an owning source, synchronize every demonstrated compatibility alias or mirror and verify both byte parity and path-sensitive behavior.
6. When changing a repo-local skill or workflow, verify that it works in a fresh checkout. Otherwise declare its external dependency and provide explicit missing-skill behavior or a portable fallback.
7. `writing-check` runs the repository update loop on every changed human-readable source.

For every changed source, use one shared budget of up to three rewrite passes after the initial check:

- remove actionable findings;
- meet FRE 55 or higher and FK 10 or lower when readability is `normal`;
- resolve actionable findings without a readability target for small, insufficient, or composition-limited samples;
- keep safety, authentication, authority, command, identifier, and other owner-designated text byte-exact unless its real owner independently authorizes a factual change; preserve the meaning of all other factual and contractual prose;
- prefer coherent compression or section rewrites when historical implementation detail obscures the current decision;
- rerun the exact source after each pass and discard stale records;
- disposition only final-source residuals after the bounded loop.

Do not chase `no_findings` by weakening contracts or rewriting known false positives. Do not bulk-disposition actionable findings merely to preserve historical prose.

### 6. Review the combined result

After all context and prose updates stabilize:

1. Run contract and documentation validators. Distinguish current repository contradictions from migration findings introduced by a newer validator schema.
2. Validate documented commands and local/published links with safe repository evidence.
3. Verify compatibility mirrors remain synchronized and every changed repo-local workflow has executable dependency or fallback behavior.
4. Run focused repository tests and documentation builds.
5. Run `context-review` on the complete diff so late prose changes cannot hide missing or duplicated context ownership.
6. Report changed files, validation, review findings, writing dispositions, and residual gaps.

Return control to the calling operator for commit, push, PR, CI, or merge decisions.

## Output contract

For large repositories, write raw records, complete ledgers, PR enrichment, and validator output to an external artifact directory. Produce a manifest with relative paths and SHA-256 digests, then keep chat output to decisions, highest-leverage drift, and the ranked Apply plan. Artifact counts and digests preserve evidence; they do not become scores or readiness gates.

Report:

- Mode: Audit or Apply
- Repository, target, and cutoff
- Context evidence completeness and GitHub enrichment
- Documentation corpus accounting
- Proposed or applied changes by owner
- Writing/readability results and bounded-pass outcomes
- Validation and context-review results
- Residual risks or unavailable evidence
- Repository write: no or yes
- Git/GitHub mutation: no
