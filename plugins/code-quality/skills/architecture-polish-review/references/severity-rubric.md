# Severity Rubric

Use this rubric during synthesis. It prioritizes architecture-polish findings without turning the review into noisy bugbot output.

## Severity

- **P0 — Blocking**: correctness, security, data-loss, migration, or rollout issue that makes the branch unsafe to merge; or architecture so confused that terminal states, ownership, or critical behavior cannot be reasoned about safely.
- **P1 — Should fix before review/merge**: major ownership, lifecycle, seam, locality, or maintainability issue that will confuse reviewers, create likely follow-up bugs, or make the feature hard to extend.
- **P2 — Polish**: improves locality, testability, validation, naming, docs, prompt/schema clarity, reviewability, or scope hygiene. Worth doing when cheap, but not necessarily merge-blocking.
- **P3 — Optional/future**: nice-to-have cleanup, future generalization, or non-blocking documentation. Do not let P3 work distract from P0/P1/P2 fixes.

## Confidence

- **0.90–1.00**: directly evidenced by code, tests, docs, or command output.
- **0.70–0.89**: strong inference from code shape or repo conventions.
- **0.50–0.69**: plausible, but owner judgment is needed. Prefer "open question" unless impact is high.
- **Below 0.50**: do not include as a finding.

## Noise suppression

- Prefer no finding over a vague finding.
- Cap the final list at roughly 7 findings unless the user asks for exhaustive output.
- Consolidate duplicates from the general pass and architecture pass.
- Rank by severity first, then confidence, then implementation leverage.
- Separate "fix before review" from "nice polish".
- Ground every finding in files, repo conventions, tests, or observed behavior.
- Do not flag pre-existing broad codebase problems unless the branch makes them worse or depends on them.

## Finding schema

```md
### [P1] <finding title>

- Confidence: 0.86
- Files:
  - `path/to/file.py`
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
```

Not every finding needs every architecture field. Include the architecture lens for findings about ownership, lifecycle, seams, module depth, locality, leverage, or tests crossing the wrong interface.
