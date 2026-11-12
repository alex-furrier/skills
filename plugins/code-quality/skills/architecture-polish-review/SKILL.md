---
name: architecture-polish-review
description: "Use when reviewing a proposed implementation in planning mode or a working branch or PR in branch-pr mode for architecture polish. Planning mode checks coherent ownership and integration before signoff; branch-pr mode grades implemented architecture and produces a cleanup plan."
---

# Architecture Polish Review

Review proposed or working code for architecture, ownership, lifecycle, seams, module depth, testability, and architecture review-readiness. `branch-pr` produces an architecture-polish grade, a path to A/A+, and an implementation-ordered cleanup plan; `planning` produces advisory integration guidance before signoff.

This skill adapts the `improve-codebase-architecture` workflow into a branch/PR
polish process. Preserve its architecture vocabulary and deepening-opportunity
lens. `provenance.json` records the source revision.

## Modes

Select the mode explicitly; do not infer it from the amount of context.

- **`branch-pr` (default for standalone invocation):** review an implemented branch or PR. It requires a diff and preserves the existing grade, code-health, and architecture-polish process below.
- **`planning`:** review a proposed solution before implementation. It requires proposed behavior, requirements and non-goals, repository evidence, known consumers, and proposed modules, interfaces, or seams. It does **not** require a Git diff, code-health evidence, or an implementation grade.

`plan` and `supervised-dev-cycle` invoke `planning` explicitly. `focused` and `thorough` are planning coverage levels, not `deep_review`; the separately approved `deep_review` escalation is unchanged.

## When to use

Use `branch-pr` when the request mentions any of:

- grade this branch / PR for architecture quality
- path to A+ or A-level architecture
- architecture polish / architecture quality polish
- working but messy code
- make this reviewable before PR or merge
- ownership, lifecycle, seam, module depth, locality, leverage, or testability concerns

Do not use as a pure bug finder or claim an overall code-quality grade from the architecture pass alone. For standalone bug/convention/completeness review, use `code-review`. When the user explicitly requests both overall code quality and architecture polish, combine one existing or newly requested broad independent-review artifact with this architecture specialist without adding a duplicate generic review.

Use `planning` for a feature-level or larger approved proposal when its integration shape needs review before implementation. Skip architecture planning for localized bug fixes, mechanical edits, established one-consumer configuration changes, and changes that preserve an existing seam.

## Bundled references

- `references/architecture-language.md` — architecture vocabulary: Module, Interface, Seam, Adapter, Depth, Locality, Leverage.
- `references/architecture-review-process.md` — forked architecture deepening process.
- `references/problem-and-design.md` — optional problem mapping, rationale and
  safe-extension lens when a consequential design choice lacks that understanding.
  Apply within the current pass in either mode; preserve proportional skip rules.
- `references/severity-rubric.md` — P0-P3, confidence, and noise suppression rules.
- `references/review-checklists.md` — selective prompts for broad migrations, async commands, generated adapters, lifecycle logs, CLI contracts, side effects, and validation reporting.
- `../code-health-review/SKILL.md` — deterministic change-shape evidence plus
  qualitative judgment about cognitive overhead, locality, proportionality, and
  evolutionary consequence.

## Planning mode

Use this mode only with an explicit `planning` request. Keep the review advisory: it does not add product scope, invent consumers, create acceptance gates from grades or severity labels, recommend a generalized seam for one concrete adapter, or prove final implementation quality. The coordinator records the review and its disposition in the existing signoff packet; only coordinator-adopted revisions become plan requirements.

### 1. Establish proportional coverage

Classify from proposed behavior, known consumers, and changed ownership or integration seams—not file count, generic risk labels, or a desire for polish:

- **Skip:** localized maintenance that preserves an established seam.
- **Focused:** feature-level or medium integration. Check affected owners, callers, lifecycle, interfaces, seams, adapters, and test implications. Prefer the smallest coherent integration; reject broad refactoring unless a directly affected invariant requires it.
- **Thorough:** large, greenfield, migration, or foundational work. Also check subsystem ownership, state and lifecycle, external adapters, compatibility/migration and recovery paths, and test seams where later correction would be expensive.

Run one planning pass at most. Do not run `branch-pr` later merely to repeat the same question. It is eligible only when the implementation introduces a named distinct question not answered by the adopted proposal, such as an unplanned lifecycle owner, leaked interface, unexpected adapter, migration path, or violated adopted seam.

### 2. Review the proposed integration

Read repository instructions and evidence for the proposed owners and known consumers. Apply the Module, Interface, Seam, Adapter, Depth, Locality, Leverage, and deletion-test vocabulary from the bundled references. Review the proposal—not an imagined diff—and distinguish required changes from optional later polish.

When the optional problem-and-design lens is selected, read
`references/problem-and-design.md` before reviewing the integration. Keep its
useful conclusions inside this same planning pass.

Fold useful conclusions into the coordinator’s existing plan when one exists;
use the standalone shape below otherwise. Do not repeat empty sections or
review-selection bookkeeping that the coordinator already owns.

Output:

```md
## Architecture Planning Review

Coverage: <focused|thorough>

### Proposed integration
<confirm the coherent shape, or name concrete changes>

### Required before implementation
- <advisory revision tied to repository evidence, affected modules/interfaces/seams, and test implication>

### Optional later polish
- <non-required improvement, if any>

### Evidence and limits
- Known consumers and repository evidence: <paths/facts>
- Not established by this review: final implementation quality or acceptance
```

The coordinator must state `adopted`, `not adopted`, or `partially adopted` for every material revision before signoff. Planning evidence remains outside final implementation-acceptance quality evidence.

## Branch/PR mode

Use this mode for explicit `branch-pr` requests and standalone invocations. It preserves the pre-existing branch/PR process.

### 1. Gather review scope

Inspect enough context to review the branch without guessing:

```bash
git status --porcelain
git branch --show-current
git diff <base>...HEAD --name-only
git diff <base>...HEAD --stat
git log <base>..HEAD --format="%h %s"
```

Infer `<base>` from the user request, PR target, upstream branch, or `main`. Warn if uncommitted changes exist and clarify whether they are included.

Read relevant context before grading:

- root and nested `AGENTS.md` / `CLAUDE.md` files for affected paths
- nearby architecture docs, ADRs, or module docs
- tests and validation commands touched by the diff
- existing Codex, bugbot, human, or PR review artifacts if already available

Do not run Codex or write a saved report file unless explicitly requested; the default deliverable is an inline review in the chat.

Calibrate depth to the reviewed diff before running the passes:

- Classify the change shape (for example: tiny docs-only/config-only, focused code change, broad feature, cross-cutting migration, CLI tool, async workflow/command, generated adapter, file-backed lifecycle state, or mutating external side effect).
- Load the relevant sections of `references/review-checklists.md` for the change shape.
- Apply the scope rules from `code-health-review`. Never skip a direct request.
  Use its requested scope when clear. Otherwise, use a focused pass for a small
  or medium change and a thorough pass for a large or repo-wide audit. For work
  without a direct request, skip the pass when a small change keeps the same owner
  and seam. This covers both local changes and mechanical changes. Run one focused
  pass on the owning module for a medium
  feature or refactor. Run one thorough pass on the affected code for a large or
  broad change, migration, new subsystem, or cross-cutting change.
  Reuse evidence that the work owner gathered for the same candidate. Give the
  architecture pass the raw deltas, high-churn overlap, evidence gaps, and four
  advisory judgments. Keep the full report out of the final review. A threshold
  can't set severity. The `strong`/`mixed`/`concerning` labels can't set the grade.
  If `uv`, Git, Ruff, or Cargo blocks the tool, report the gap and continue with the qualitative code-health pass.
  If the `code-health-review` skill itself is unavailable, report the incomplete
  plugin install and avoid claiming code-health evidence.
- When a change promotes heuristic categories, normalization, scores, thresholds, templates, or model-facing summaries into an interface or action gate, load `avoiding-ai-antipatterns` and its `resources/heuristic-authority.md`. Apply its loss, named-consumer, and authority-boundary tests as a selective architecture lens. When delegating the architecture pass, supply the selected resource path and require the child to read it before reviewing.
- For tiny docs-only or config-only diffs, still provide the grade, relevant dimension grades, and path to A/A+, but keep the review concise and proportionate.
- Do not manufacture architecture findings to satisfy the template. If no branch-caused P0-P3 finding or deepening opportunity is directly evidenced, say so explicitly and keep the path to A/A+ to small file-grounded polish, validation, or merge-readiness checks.

### 2. Run the architecture specialist pass

Consume any existing broad-review artifact as context, but do not launch a general-quality reviewer from this skill. Run one read-only architecture specialist when subagents are available. Load `references/architecture-language.md` and `references/architecture-review-process.md` for the pass. If subagents are unavailable, run the pass inline after reading those references.

Select the problem-and-design lens when explicitly requested or when a
consequential choice lacks a supported problem mapping, rationale or extension
path. Read `references/problem-and-design.md` when selected. For a delegated
pass, supply its resolved path and the concrete design question, and require the
specialist to read it before reviewing. For an inline pass, apply it directly.
Otherwise skip this optional lens; do not add a pass or report.

Subagent/task prompt:

```text
Review this branch/PR using the architecture-polish vocabulary and process. Use Module, Interface, Seam, Adapter, Depth, Locality, Leverage, and the deletion test. Find deepening opportunities and testability implications. Do not edit files.

If the parent selected the problem-and-design lens, first read the supplied
`references/problem-and-design.md` path and apply it to the supplied design
question. Ground problem correspondence and rationale in evidence, rehearse a
useful extension only when known, and preserve scope and local contracts. Fold
useful conclusions into this pass; add no separate report or required refactor.

If the parent selected the heuristic-authority lens, first read the supplied `avoiding-ai-antipatterns/resources/heuristic-authority.md` path and apply its full finding, correction, severity, and earned-structure contract.

Focus on ownership, lifecycle, module depth, leaky interfaces, shallow pass-through modules, complexity spread across callers, tests crossing the wrong seam, branch-scale seam maps for broad migrations, parity/characterization tests before extraction, and places where one adapter is being generalized before a second adapter exists. When the heuristic-authority lens was selected, require concrete evidence loss or unsupported proxy authority; do not flag exact structure serving a named deterministic consumer. If the diff does not directly evidence a real architecture deepening opportunity, report that none were found instead of inventing one.

Use any supplied code-health findings to choose where to inspect, then apply the
deletion test, locality, ownership, and concrete-consequence standards. A large
or complex function may still be a coherent deep module.
```

Expected output:

```md
## Architecture Deepening Opportunities

No architecture deepening opportunities found for this diff.
```

Or, when directly evidenced:

```md
## Architecture Deepening Opportunities

1. **<candidate title>**
   - Files:
   - Module/interface/seam involved:
   - Problem:
   - Solution:
   - Benefits:
     - Locality:
     - Leverage:
     - Test impact:
   - Deletion test:
```

### 3. Synthesize the architecture polish review

Read `references/severity-rubric.md`. Synthesize the architecture specialist result with supplied broad-review and code-health evidence without repeating their general-quality review. Deduplicate overlapping concerns and cap the final finding list around 7 items unless exhaustive output is requested. Grades and P labels prioritize this review; they do not independently mint acceptance gates. A finding blocks only when current evidence proves approved behavior false, proves an applicable repository or external invariant or contract was violated, or establishes a concrete credible critical correctness or safety failure affecting the claimed behavior or effect. Do not defer a known critical bug as polish.

Scale the final output to the diff shape identified in Step 1. For tiny docs-only/config-only diffs, keep the architecture assessment concise and allow `No P0-P3 findings` when the evidence does not support a finding.

Final output:

```md
## Architecture Polish Review

### Architecture-polish grade

Current architecture: <grade>
Target architecture: A/A+

### Code current state

<what exists, what changed, and which modules own which behavior>

### Branch-scale seams

<for broad migrations/features only: name the main seams such as ingress/CLI, application/lifecycle, persistence/ledger, policy, side-effect adapters, rendering/output, and legacy compatibility surface. Omit or keep brief for focused diffs.>

### Dimension grades

<architecture-specific dimensions supported by the specialist pass and supplied evidence>

- <dimension>: <grade> — <evidence and what would improve it>

### Findings

No P0-P3 findings.

Or, when directly evidenced:

### [<P0|P1|P2|P3>] <finding title>

- Confidence: <0.00-1.00>
- Files:
  - `path`
- Issue:
- Why it matters:
- Architecture lens:
  - Module:
  - Interface:
  - Seam:
  - Locality/leverage impact:
- Proposed improvement:
- Implementation difficulty: S / M / L
- Verification:

### Recommended implementation order

1. ...

### Verification plan

```bash
<commands>
```

Note which commands were run, skipped, blocked, or not applicable. If a validation command fails for an environment or pre-existing reason, report it separately from branch findings.

### Re-grade criteria

- A when ...
- A+ when ...
```

Implementation-order heuristic:

1. P0 correctness, safety, migration, or rollout issues.
2. P1 ownership/lifecycle/seam issues.
3. P1/P2 extraction that unlocks simpler tests or clearer review.
4. P2 prompt/schema/docs/test clarity.
5. P3 future generalization only after multiple concrete uses exist.
6. Validation.
7. Re-grade.

### 4. Implement only when requested

If asked to fix findings, work through the implementation order in small chunks. After each chunk, run focused validation and update the grade. Do not auto-commit unless explicitly asked.

### 5. Propose durable capture

If the review reveals a reusable repo convention, propose where to document it: repo docs, AGENTS.md, a skill, or a vault note. Do not edit durable context without approval.

## Output discipline

Apply `user-facing-response` in normal mode to a substantial conversational review
or cleanup plan after preserving this skill's grade, evidence, and implementation
order. If `user-facing-response` is unavailable, keep this output contract and draft
the review directly without invoking Vale by default.

- Lead with the grade and highest-leverage fixes.
- Keep findings actionable and file-grounded.
- Prefer fewer, sharper findings over exhaustive commentary.
- Distinguish "should fix before review" from "nice polish."
- Avoid speculative framework extraction when only one adapter/use case exists.

## Optional integrations

`plan`, `supervised-dev-cycle`, `research`, `skill-search`, and writing skills
are optional callers or aids, not prerequisites. If absent, gather repository
evidence and draft the same review inline; report material evidence gaps rather
than inventing evidence or adding gates. Publication remains with the authorized
repository owner.
