---
name: user-facing-response
description: Draft substantial user-facing plans, explanations, recommendations, summaries, and handoffs as clear conversational prose, or explicitly rewrite the immediately preceding assistant response in plain English with source-bound advisory checks. Use when a general agent-facing response does not require a configured external voice owner.
---

# User-Facing Response

## Use this after the domain owner establishes the facts

Shape substantial conversational prose without taking over facts, decisions, technical depth, safety, authority, or required structure. Use neutral prose unless a configured external voice owner is available.

Choose **normal mode** for a substantial plan, explanation, recommendation, summary, or handoff. Choose **explicit plain-English rewrite mode** only when the user asks to simplify clearly bounded pasted text or the immediately preceding assistant response. Do not infer rewrite mode from requests to be clear, concise, polished, or scannable. Skip this skill for short confirmations, exact quotations, raw command output, and artifacts with a destination voice owner.

## Writing Check dependency

This skill invokes the independently distributed `safurrier-writing-check` package only for explicit plain-English rewrites. From a checkout of this catalog, install it with `uv tool install ./packages/writing-check`; then `writing-check --help` is available without another setup command. If the command is missing or returns `unavailable` or `execution_error`, complete the preservation-checked rewrite, report that advisory check as unavailable, and do not substitute another linter.

## Normal mode

1. Keep the active domain skill responsible for facts, decisions, and output contract.
2. Apply `writing-core`: lead with the outcome or recommendation, group related context, and make the next action easy to find.
3. Return the useful response without narrating the writing process.

Do not run `writing-check` or Vale by default. If `writing-core` is unavailable, continue with the domain owner’s contract and these preservation boundaries; do not substitute a checker or block the response.

## Explicit plain-English rewrite

1. Confirm the source is bounded pasted text or only the immediately preceding assistant response. Never search older responses or combine sources. If no exact source is available, ask the user to provide it.
2. Create a preservation ledger for facts, decisions, uncertainty, qualifications, unresolved questions, exact commands, identifiers, links, quoted text, warnings, code, and billing, authentication, authority, and safety language.
3. Rewrite in plain English. Simplify sentence structure and explain needed technical terms, but keep exact searchable terms when replacing them loses precision.
4. Compare the candidate with the ledger. Do not invent facts, omit decisions, weaken qualifications, broaden permission, soften warnings, or change authority or safety boundaries.
5. Save the exact UTF-8 candidate and run:

   ```bash
   writing-check --profile user-facing-response --json <candidate.md>
   ```

6. Confirm the returned text and `source.sha256` identify that exact candidate. Treat findings and readability as advisory evidence, not a gate, score, factual judgment, or authorization.
7. Independently justify each fix, or retain the exact term, quote, required text, or safety/authority constraint. Discard dispositions whenever the candidate changes.
8. For a `normal` sample below FRE 55 or above FK 10, optionally make at most three focused, preservation-checked revisions and rerun the source-bound check. Do not revise merely for a metric or apply this opportunity to `small_sample`, `insufficient_sample`, `composition_limited`, `disabled`, `unavailable`, or `execution_error`.

If Writing Check or Vale is missing, complete the preservation-checked rewrite and report the advisory check as unavailable. Do not substitute another linter or claim clean evidence. Return the rewrite even when findings or observations remain, mentioning an unavailable check or protected constraint only when it materially explains the result.

## Non-negotiable boundary

Keep bytes exact only for a real exact-byte consumer: the candidate supplied to Writing Check and its source digest; policy, config, rule, and license integrity assets; machine-consumed command syntax and identifiers; and text the user or owning contract explicitly marks exact. Preserve the meaning, qualifications, and safety, authentication, authority, factual, and contractual constraints of all other prose. A checker suggestion alone never authorizes a factual or constraint-changing edit. Preserve the domain owner’s meaningful structure and the user’s intent; conversational polish cannot override commands, identifiers, code, warnings, safety constraints, factual uncertainty, release, or approval authority.
