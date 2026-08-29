---
name: pr-description
description: Draft, improve, or audit pull request descriptions that explain intent, behavioral change, reviewer-relevant composition, and developer-centered evidence. Use when preparing PR copy after reading the complete final change; do not mutate Git or GitHub or perform code review.
---

# PR Description

Give an unfamiliar reviewer the most understanding per word. Own the reviewer journey, behavioral before/after, and developer-centered evidence; leave every Git or GitHub mutation to the calling workflow. Passing Vale or readability targets never substitutes for this semantic contract.

## Modes

- **Draft:** compose from a branch, commit range, or existing PR evidence.
- **Improve:** revise an existing body surgically while preserving accurate human prose.
- **Audit:** report concrete friction and findings without rewriting unless requested.

## Gather the final change

Establish base and head. Read the complete commit range, final diff, linked issue or design context, repository instructions, and observed validation. For an existing PR, also inspect the title, body, scope-changing comments, files, and current patch. Treat existing copy and commits as claims to verify, not ground truth.

Do not invent intent, impact, risk, results, rollout state, issue links, or metrics. Ask for missing author context when it materially changes the body.

## Use one contract

Every ready-to-paste Draft or Improve body MUST use these exact headings in this order:

```markdown
## Why
## What changed
## Evidence
```

Apply this contract regardless of diff size, changed-line count, prior body length, prior prose quality, or readability sample size. Keep it proportional: a local obvious change is usually under 120 words, a medium behavior or workflow change under 300, and a cross-system or migration change under 500. These are ceilings, not targets, and control depth only. A very small body can keep each section to one sentence; never omit or replace a required heading.

### Why

State the pre-change problem, why work was needed, and the important user or system consequence. Lead with verified behavior, not a title repeat or feature inventory.

### What changed

Explain the behavioral before/after. Group details by concepts rather than files or commits. For behavior that crosses multiple components, include a short useful happy path so the handoff between components is understandable. Add one concrete example when it materially clarifies input, output, migration, failure behavior, or authority.

For a large or multi-component flow, put the happy-path example in a collapsed `<details>` block when the explanation would otherwise interrupt the main path. Include one small GitHub-native Mermaid diagram when the component handoff is faster to understand visually. Keep it to the normal path, at most eight nodes, and omit it when prose is clearer. Pair the diagram with the concrete input/outcome example; do not add architecture decoration or a second review-guide surface.

````markdown
<details>
<summary>Happy path example</summary>

```mermaid
flowchart LR
  A[Domain skill drafts] --> B[Writing Check observes]
  B --> C[Domain skill judges findings]
  C --> D[GitHub Open PR verifies and publishes]
```

A required qualifier can remain even when Vale flags it; the final source is checked again before publication.

</details>
````

Preserve exact commands, identifiers, links, machine-managed blocks, warnings, billing or authentication facts, and safety or authority language. Only the owning domain skill or a human can judge whether those facts may change.

For a diff with strictly more than 500 Git textual changed-line events, run the helper against the exact base and head through the repository-owned Python environment. This threshold controls only optional change-shape detail inside `What changed`; it never controls skill activation, required headings, semantic evidence, or final Writing Check:

```bash
python3 <skill-dir>/scripts/pr_change_shape.py BASE HEAD --repo REPO
```

After assigning every core path to a conceptual group, render the Markdown with:

```bash
python3 <skill-dir>/scripts/pr_change_shape.py BASE HEAD --repo REPO \
  --markdown --groups-json /tmp/pr-change-groups.json
```

The helper disables external diff and text conversion, parses NUL-delimited raw and numstat records, queries tree-specific attributes, and returns exact per-file additions and deletions. It classifies one accounting dimension: `core` or a folded `supporting` category covering tests, fixtures, docs, config, manifests, lockfiles, generated/vendored material, and similar supporting artifacts.

The helper does not invent conceptual groups. Assign every core path to at most five change-specific conceptual groups in a JSON mapping, then ask the helper to render the table. Put the summary table in `What changed`. It must show totals, core conceptual groups, one folded supporting category, and this meaning: additions + deletions describe diff shape; modified lines can count twice; the numbers are not effort, risk, quality, review time, or readiness. Keep binary and submodule changes visible without invented line counts. Exactly 500 does not trigger the table, though composition can justify showing it earlier.

For reviewer drill-down, render two collapsed inventories beneath the summary:

- **Core changes:** list every core file under its conceptual group with additions, deletions, changed-line events, and a subtotal for each group.
- **Supporting changes:** show totals by supporting kind, then list every supporting file with its kind and counts plus subtotals.

The collapsed inventories preserve the complete mapping without forcing reviewers through a file wall. Keep actual paths mechanically sourced from the helper. Never invent a file, move a supporting file into a conceptual group for narrative balance, or let the detailed tables replace the behavioral before/after explanation.

### Evidence

For each materially different claim, say:

1. what validation passed or what outcome was observed;
2. what behavior, failure, or boundary it exercised;
3. why a developer or reviewer should care.

Use a short bold headline with one or two indented bullets when the evidence sentence becomes dense. The first sub-bullet names the observed validation and exercised behavior. The second explains the developer or reviewer benefit. Keep a single sentence when it is already easy to scan. Aggregate checks that support the same claim. Do not list commands, check names, Harness Kit records, agents, bot status, or repetitive assurance disclaimers. Include one remaining-gap note when it helps the reviewer avoid a likely overclaim. A narrow support statement often needs no separate disclaimer.

Good:

```markdown
- **Broken checks cannot look clean.**
  - Missing Vale and malformed output produce explicit unavailable and execution-error records while retaining source identity.
  - Authors will not mistake a broken checker for clean writing evidence.
```

Avoid:

```markdown
- `uv run pytest ...` passed. This does not prove production safety.
```

## Add optional sections only for real facts

After the three required sections, add `Decision needed`, `Migration`, or `Rollout` only when the final change contains a real unresolved human choice, migration obligation, or rollout behavior. Do not add empty headings. Remove generic reviewer questions; never generate a question section merely because the diff is large. Put verified review-critical design constraints in `What changed` instead.

## Preserve before rewriting

In Improve mode, keep accurate, specific, useful human wording verbatim where practical, but reorganize it under the required contract. Prior body length or prose quality never preserves a nonconforming structure. Edit only for a factual mismatch, missing review-critical context, weak hierarchy, duplication, synthetic prose, stale evidence, or contract compliance. Preserve required text, issue-closing lines, links, credits, checklists, disclosures, and author uncertainty.

Treat machine-managed marker blocks separately. Never rewrite inside them. The mutation-owning caller must merge them byte-for-byte around authored copy and stop when ownership or placement is unclear.

## Run the advisory check on the final candidate

After semantic drafting and after every revision, always run `writing-check --profile pr-description` on the exact final candidate. Run it for every candidate, including `insufficient_sample` and `small_sample` results; sample size controls only readability applicability. Confirm its retained text and `source.sha256` match the bytes handed to the mutation owner.

- The profile uses the broad reviewed portable policy plus narrow mechanical host terminology; it excludes upstream Google word-list substitutions.
- Findings are a review queue, not a quality failure. In Draft or Improve mode, fix or explicitly disposition every finding against this exact `source.sha256`.
- Readability is private and advisory: insufficient below 100 prose words or 5 sentences, small below 200 words or 8 sentences, normal at 200 words and 8 sentences with FRE 55 / FK 10 observations.
- Never print readability in the public body by default.
- A destination owner can retain exact terms, quotes, required text, or voice with a source-bound disposition while leaving the base policy visible.
- Complete disposition accounting is not a quality, readiness, or publication gate.
- Report `input_error`, `unavailable`, or `execution_error` explicitly. Never convert them to `no_findings`.
- If authored copy or a managed block changes after checking, discard the stale record and re-run the checker.

For a `normal` sample below FRE 55 or above FK 10, make a focused rewrite and rerun the exact candidate. Repeat for no more than three total rewrite passes, stopping early only when both targets are met. Preserve technical meaning, exact commands, identifiers, links, warnings, authentication and billing facts, required text, and authority boundaries on every pass. Never game the formulas or expand familiar technical terms merely to change a score. After three misses, retain precise or owner-required language and report the final metrics, attempted improvements, and residual dense sections; do not turn the advisory target into a gate.

A clean Writing Check record does not prove that the body follows the required headings, explains behavioral before/after, or provides developer-centered evidence. Verify those semantic duties separately before returning the candidate.

## Return

For Draft, return the body plus a short private note only when unresolved author facts or required text need attention.

For Improve, return one caller decision before the copy:

- `No body change needed` only when the current body already uses the exact required headings, satisfies the semantic evidence guidance, remains accurate and reviewable, and has a current final-candidate Writing Check record.
- `Apply revision: reason` when the body misses any required heading or semantic duty, the checker record is stale or unusable, or a verified mismatch or material reviewer friction warrants a change.

Exclude that decision line from the public body. For Audit, load [the rubric](references/rubric.md), cite evidence, and name the few highest-value fixes without rewriting.
