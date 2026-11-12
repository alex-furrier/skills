# PR Description Rubric

Use this fixed rubric for audits and dogfood comparisons. Score each dimension from 0 to 2. Cite the description and diff evidence behind the score.

## Scoring

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Factual grounding | Unsupported or contradicted claims | Mostly accurate, with ambiguity or unchecked claims | Important claims verified against the final diff and explicit context |
| Problem and intent | Reason is absent or generic | Reason is implied or arrives late | Reviewer quickly understands the pre-change problem and why work was needed |
| Conceptual change | Diff or file narration | Behavior is described but the mental model is incomplete | Important before/after behavior or architecture is clear without walking files |
| Impact, risk, and limits | Missing, boilerplate, or overstated | Some material effects or limits appear | The compact `Risk` section preserves the upstream assessment and uncertainty, or explicitly reports missing input; material impact and limits are honest and proportionate |
| Evidence quality | Transcript, command inventory, or unsupported confidence | Relevant proof appears but dense prose hides why a developer cares | Scannable claim headlines connect observed outcomes to exercised behavior and developer confidence; one gap note covers material uncertainty |
| Proportion and hierarchy | Size/structure obstructs review | Mostly scannable with repetition or misplaced detail | Depth matches complexity and high-value context comes first |
| Preservation in Improve mode | Useful human context is lost | Main ideas survive but wording or nuance is needlessly replaced | Accurate, distinctive prose and required text stay intact; edits are surgical |
| Reviewer navigation | Generic questions, tutorial, or uncollapsed file wall obstructs review | Important concepts are present but hard to enter | `What changed` supplies the smallest useful happy path, example, or conceptual order; large multi-component flows may use one collapsed Mermaid example and triggered change shape has collapsed core/supporting file inventories |

`Preservation` is not applicable in Draft mode. Report it as `N/A` and compare totals over the remaining 14 points. Do not award points for polish alone.

## Hard failures

Mark the audit `Needs revision` regardless of total score when any of these occur:

- a material claim conflicts with the final diff or supplied evidence;
- rationale, impact, results, or confidence are invented;
- useful human-written context is removed in Improve mode without a factual or reviewability reason;
- internal agent/Harness Kit activity or a raw validation transcript overwhelms the change;
- the output mutates GitHub or becomes an automated review/onboarding artifact instead of PR copy;
- the body omits `Why`, `What changed`, `Risk`, or `Evidence`;
- the Risk section invents a rating, loses material upstream uncertainty, or turns an advisory recommendation into approval;
- a triggered change-shape summary omits exact totals, folds core work into supporting changes, lacks mechanically sourced collapsed core/supporting file inventories with subtotals, or implies effort, risk, quality, or readiness;
- evidence is a raw command/check inventory instead of observed behavior and developer relevance.

## Verdict

- **Ready:** no hard failure, every applicable dimension scores at least 1, and at least 80% of available points.
- **Needs a small edit:** no hard failure and at least 65%, with a few specific fixes.
- **Needs revision:** any hard failure, an applicable zero, or less than 65%.

## Audit output

Report:

1. verdict and total;
2. one evidence-backed line per dimension;
3. up to three highest-value changes;
4. claims that still require author confirmation;
5. useful original wording to preserve.

Do not rewrite in Audit mode unless requested.
