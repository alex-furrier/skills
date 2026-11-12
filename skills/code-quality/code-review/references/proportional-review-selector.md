# Proportional Generic Review Selector

The selecting owner (the caller, or this skill when invoked directly) selects proportional review. Consume an existing caller selection without weakening
it. Record the fixed request and approved intent when generic review is selected.
Do not require a separate planning workflow merely to choose no independent review.
The selecting owner also retains question-driven specialist selection. Never
select a specialist solely from a path, diff size, risk label, or reviewer priority.

## Inputs and output

Inspect the local committed merge base and immutable candidate HEAD, applicable repository and human requirements, deterministic evidence, approved intent, existing exact-scope evidence, and any named specialist questions. Record selected and skipped
lanes with their reason. The generic-review output is exactly one profile:

| Profile | Lanes | Select only when |
| --- | --- | --- |
| `deterministic-only` | none | Purpose-built deterministic proof covers every credible failure in the requested scope, no named independent judgment remains, and no policy floor requires independent review. A code edit is not by itself a reason to reject this profile. |
| `bug-hunter` | `bug_hunter` | A bounded code or semantic-configuration change can introduce a defect that deterministic proof cannot exclude. This is the normal independent-review default. |
| `repository-fit-completeness` | `repository_fit`, `completeness` | A named integration question concerns a canonical mechanism, consumer, registration, lifecycle, migration, compatibility, or approved adjacent obligation. Use alone only when no independent defect judgment is needed. |
| `bug-hunter-fit-completeness` | `bug_hunter`, `repository_fit`, `completeness` | Both a bounded defect judgment and a named integration question remain unresolved. |
| `full` | `diff`, `repository_fit`, `completeness`, `bug_hunter` | An explicit repository/human policy requires it, or several independently coupled behavioral seams, a multi-consumer migration/refactor, unfamiliar weakly-owned code, or distinct unresolved generic questions make all four lanes useful. |

Repository or human requirements are a floor: never choose a weaker profile.
File count, production/security labels, and diff size are signals, never rules.
A named security or domain uncertainty selects a matching specialist when one
owns it; it does not automatically select `full`.

## Advisory product experience pass

Run `product-door-policy` once during review when the change materially affects
a participant's journey: entry/onboarding, primary choices, navigation, feature
mix, feedback, or return/recovery. Include CLI and agent-facing workflows, not
only visual interfaces. Scope the pass to the affected journey in its product
context; do not audit the entire repository on every PR. Honor an explicit
product-review request at any size. Otherwise skip mechanical/internal-only
changes, cosmetic edits that preserve the experience, and repairs that merely
restore settled behavior without changing an experience choice.

The selecting owner runs the pass before handoff,
or reuses an existing review that covers the same journey and candidate behavior. Consolidate with an already-selected domain reviewer when it can apply the
full product skill to this distinct question. Keep the pass separate from the
generic profile and ordered lanes; it is not a fifth code-review lane, a required
external workflow review, or a new CI check. Record a concise run/reuse/skip/unavailable reason.

Treat `product-door-policy`, `product-experience-brief`, and `skill-search` as
optional external integrations, not catalog dependencies. If an integration is
absent, record the question as unanswered and continue without installing tools
or bypassing access boundaries; do not require another missing skill as fallback.

Use the existing experience brief or let the skill recover intent. For unresolved
intent, state assumptions and conditional suggestions without turning this
automatic advisory pass into a blocking interview. Report source/runtime limits.
If the skill or an authorized execution route is unavailable, report the gap and
continue required work; do not install tools, change providers, or imply a clean
review. Revisit the pass only when later changes affect its experience judgment.

Surface up to three material, nonduplicate findings in the user-facing handoff
as **Product/UX suggestions (advisory)**. State the concrete experience, why it
matters, the suggested direction and tradeoff, and any consequential uncertainty
or small next check. Reuse the existing PR summary when useful and publication
is authorized; do not create a separate report or post comments just to announce
the pass. A report link alone must not replace presenting the useful findings.
With no material findings, use at most a short completion note; invent no quota.

Keep these suggestions advisory in any formal acceptance rubric. Their presence,
severity labels, unavailable review, or an unanswered product question must not
block publication, readiness, or completion, create a risk-acceptance request,
or trigger an automatic redesign/repair loop. Present product changes for owner
adoption before expanding scope. If the pass identifies a concrete violation of
already-approved behavior, an applicable contract, or a critical correctness or
safety failure, verify and route that defect through the existing review boundary;
the advisory label does not waive real defects or other required checks.

## Immutable snapshot and repair

1. Before publication, record repository, merge base, and committed HEAD. Run all selected generic review lanes against that snapshot. Complete formal implementation acceptance when required by the caller or repository, otherwise compare the outcome and proof directly with the request.
2. Publish only after applicable checks, selected review, and any required formal acceptance are satisfied. After publication, the authorized publication owner runs CI and GitHub-specific review against the published snapshot without adding a new default review panel.
3. Deduplicate findings by violated invariant and make one repair batch. Classify the batch. **Bounded** means it addresses named findings without a
   new mechanism, interface, ownership boundary, dependency, migration,
   lifecycle, or architecture. Anything else is **scope-expanding**.
4. For a bounded repair, retain prior fit/completeness/full/specialist artifacts
   as ancestor evidence with their original HEAD; rerun affected deterministic
   proof and directly verify the repair. If generic independent review was
   selected, run an exact-final-HEAD `bug_hunter` over the complete branch diff.
   Rerun another lane or specialist only when its owned question changed.
5. For scope expansion, invalidate the prior selection and perform full
   reselection. Never relabel ancestor evidence as an exact-final-HEAD review.

The authorized publication owner returns lifecycle readiness, snapshot, CI
evidence, generic review evidence, external-review dispositions, repair lineage,
and invalidated criteria. Review selection does not authorize publication or
calculate implementation acceptance. Optional `github-open-pr` may own this
workflow; if absent, return evidence to the repository owner and report any
required publication gap without publishing.
