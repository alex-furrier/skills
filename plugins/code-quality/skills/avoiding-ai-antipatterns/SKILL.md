---
name: avoiding-ai-antipatterns
description: "Reviews code changes and selectively reviews plans, technical designs, and agent workflows for AI-generated smells. This skill should be used during code review or preflight; when a plan gives heuristic labels or summaries unsupported authority; or when it mandates final-form assurance before evidence, an actual consumer, or a credible consequence earns it. Exact typed or machine-consumed structure alone is not a smell."
---

# Overview

Review the artifact in front of the agent rather than forcing every task through one checklist:

- For code changes, cross-reference the diff against the [Universal DO NOT DO List](resources/01-anti-patterns-core-universal-do-not-do-list.md).
- For plans, designs, schemas, protocols, evaluators, and agent-facing tools that introduce semantic categories or summaries, load [Heuristic Authority and Irreversible Semantic Compression](resources/heuristic-authority.md).
- For plans, designs, and agent workflows that prescribe final-form attestation, fixed evidence sequencing, or review-created gates before a consumer or consequence is known, load [Premature Final-Attestation / Speculative Completeness](resources/premature-assurance.md).

Do not run the code-only blocking checklist against a plan with no code. Apply only the smell relevant to the artifact and concrete evidence. The two planning resources are independent lenses; load one or both only when their trigger is present.

## Activation Signals

- Running `/pr-preflight` or `/review` commands
- Code review of any changes (AI-generated or not)
- Reviewing an implementation plan, technical design, schema, protocol, evaluator, or agent workflow
- A proposal introduces canonical categories, normalization, scores, thresholds, templates, decision tables, or model-facing summaries
- A proposal requires immutable snapshots, exact provenance, fixed validation phases, or reviewer-created gates without naming the consumer or consequence
- Before committing changes

## How to Check

### 1. Select the relevant review surface

- **Code diff:** inspect changed behavior and load the core code-review list.
- **Plan or design:** inspect proposed commitments, interfaces, evidence sequencing, and action gates. Load only the planning resource or resources whose trigger is present.
- **Mixed artifact:** review code and design commitments separately; do not let a clean result in one imply a clean result in the other.

### 2. Get the changes to review

```bash
# Unstaged changes
git diff

# Staged changes
git diff --cached

# All changes on branch vs main
git diff main...HEAD

# Changed files only
git diff main...HEAD --name-only
```

### 3. Cross-reference against anti-patterns

Read [resources/01-anti-patterns-core-universal-do-not-do-list.md](resources/01-anti-patterns-core-universal-do-not-do-list.md)
and check each change against the forbidden patterns.

## Blocking Anti-Patterns Checklist

These MUST NOT be present. Fail the review if found.

- [ ] **No silent fallbacks** - Code raises errors instead of returning defaults
- [ ] **No inline imports** - All imports at module level (exception: circular dependency avoidance, which is a code smell)
- [ ] **No nested function/class definitions** - Defined at module level
- [ ] **No `Any` type hints** - Types are specific
- [ ] **No `getattr` for known attributes** - Direct attribute access only
- [ ] **No backwards-compat shims** - Clean refactors, updated call sites
- [ ] **No catch-all exception handlers** - Specific exception types only

## Testing Anti-Patterns Checklist

- [ ] **No over-mocking** - Prefer fakes, doubles, stubs in conftest over inline mocks
- [ ] **Tests behavior, not implementation** - Prefer observable behavior, parsed/semantic output, or the actual consuming interface over incidental byte identity, raw-text snapshots, and wording. Introduce an exact-byte gate only on explicit user request; inventory existing gates for possible removal even when they protect a current consumer, and do not remove safety checks during review; see the core testing guidance. Assert public CLI/protocol/diagnostic/generated-source string contracts where relevant.
- [ ] **Reusable fixtures** - Test utilities belong in conftest, not duplicated per test

## Taste-Based Review (Non-Blocking)

These don't fail the review but should be noted if observed.

### Abstraction Weight
Call out if an abstraction doesn't earn its keep:
- Does it reduce complexity or add a layer of indirection?
- Is the interface clear or does it obscure what's happening?
- Would inline code be simpler to understand?

### Codebase Cohesion
Call out if code ignores existing patterns:
- Does it follow conventions already established in the codebase?
- Does it introduce new patterns where existing ones would work?
- Does the codebase feel more or less cohesive after this change?

## Heuristic Authority Review

When a change turns ambiguous evidence into labels, scores, normalized records, templates, thresholds, or decision tables, load [resources/heuristic-authority.md](resources/heuristic-authority.md).

Treat the construct as a review lead, not a finding. Evaluate it independently from Premature Assurance. A control standing in for consumer compatibility or completion does not by itself prove irreversible semantic compression. Do not copy a Premature Assurance finding into this namespace unless the artifact separately establishes source-evidence loss, downstream authority, consequence, and an evidence-restoring correction.

Report heuristic authority only when the evidence supports all of these:

- source observations are compressed or hidden, or a proxy substitutes for a semantic judgment it cannot establish;
- the design causes concrete information loss, false precision, coupling, or unsafe behavior;
- the derived value controls an action, gate, public interface, persisted truth, or evidence shown to a model;
- no named deterministic consumer requires that exact semantic commitment; and
- a smaller correction can restore evidence or remove unsupported authority without weakening a real machine or safety invariant.

Do not flag schemas, enums, state machines, or exact protocol fields merely for being structured. Do not weaken signature, identity, authorization, idempotency, acknowledgement, audit, dependency, or fail-closed lifecycle boundaries while reviewing an existing byte gate. Inventory the gate separately for owner-authorized retention or replacement.

## Premature Assurance Review

When a plan, design, or workflow mandates final-form attestation or a fixed proof sequence before evidence identifies what must be distinguished, load [resources/premature-assurance.md](resources/premature-assurance.md). Require concrete evidence of unsupported proxy authority or non-discriminating ceremony. Default-deny new commit-hash, byte-equivalence, digest, immutable-provenance, and parity gates unless the user explicitly requests them. A cited contract or credible consequence identifies a follow-up question, not permission to introduce a gate. Inventory existing gates, including review workflow and security gates, as candidates for removal; name their consumers and effects, and seek an owner decision before weakening any authorization, integrity, external-effect, or state-preservation boundary.

## Output Format

Keep independent review surfaces in independent verdict namespaces. A blocking code or testing anti-pattern does not make either planning lens a finding, and a planning-lens finding does not establish the code verdict. One fact may support findings in two lenses only when each lens independently satisfies its complete threshold and correction contract; shared vocabulary or proxy substitution is not enough. The caller owns any combined acceptance decision.

Issue a blocking code verdict only from the complete changed code and required context. When the supplied artifact contains only summaries or selected excerpts, record the missing code evidence rather than inferring checklist failures from an incomplete surface.

For each selected planning lens, keep its evidence, rationale, consequence, and correction under that lens's namespace and return one target verdict:

- `FINDING` — every required finding element is supported by cited artifact evidence;
- `NO_FINDING` — the lens was assessed, the available evidence is sufficient, and its threshold is not met; or
- `INSUFFICIENT_EVIDENCE` — a missing fact could change whether the threshold is met.

Use `NOT_APPLICABLE` only when a lens trigger is absent and the lens was not selected. Keep generic observations limited to evidence that belongs to none of the selected lens verdicts.

A Premature Assurance `FINDING` is invalid unless it cites the current decision, displaced discriminating observation, disputed control, authority or consumer, attributable consequence, smallest preserving correction, and earned boundaries that remain exact. Put generic code, testing, maintainability, or workflow observations outside that target verdict.

Use the template below for code review. For plan/design review, use the surrounding review format and report only concrete findings with the selected lens verdict and its required evidence. A clean plan/design review does not require checklist recitation.

```markdown
## Anti-Pattern Review

### Blocking Issues
- [ ] FAIL: Inline import at src/foo.py:42
- [ ] FAIL: Silent fallback at src/bar.py:15

### Testing Issues
- [ ] WARN: Over-mocking in tests/test_foo.py - consider conftest fixture

### Observations
- src/utils.py:50 - `DataProcessor` class adds indirection without benefit;
  the three methods could be standalone functions
- src/api.py - Uses custom retry logic instead of existing `@with_retry`
  decorator from utils/retry.py

### Verdict
🔴 BLOCKING ISSUES FOUND | 🟡 WARNINGS ONLY | 🟢 CLEAN
```
