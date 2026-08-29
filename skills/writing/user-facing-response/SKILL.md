---
name: user-facing-response
description: Draft substantial user-facing plans, explanations, recommendations, summaries, and handoffs as clear conversational prose, or explicitly rewrite the immediately preceding assistant response in plain English with source-bound advisory checks. Use when a general agent-facing response does not require a configured external voice owner.
---

# User-Facing Response

Shape general conversational prose after the domain owner has established the facts, decisions, and output contract. A configured external voice owner may handle destination-specific voice; when absent, use neutral prose.

## Choose a mode

- Select **normal mode** for a substantial user-facing plan, explanation, recommendation, summary, or handoff.
- Select **explicit plain-English rewrite mode** only when the user directly asks to rewrite the immediately preceding assistant response or clearly bounded text they pasted in plain English, simpler language, or equivalent wording.
- Do not infer rewrite mode from a general request to be clear, concise, polished, or easier to scan.
- Skip this skill for short confirmations, exact quotations, raw command output, and artifacts whose destination owner already controls the final prose.

## Normal mode

1. Keep the active domain skill or workflow responsible for facts, decisions, technical depth, safety, authority, and required structure.
2. Apply `writing-core` to substantial conversational prose after satisfying that contract. Lead with the outcome or recommendation, group related context, and make the next action easy to find.
3. Return the useful response without narrating the writing process.
4. Do not run `writing-check` or Vale by default in normal mode.

If `writing-core` is missing, continue directly with the domain owner's contract and this skill's preservation boundary. Do not substitute a style checker or block the response.

## Explicit plain-English rewrite mode

Enter this mode only for an explicit request to rewrite existing text in plain English or equivalent simpler language. Do not infer this mode from a general request for clear or concise prose. When the request includes clearly bounded pasted source, use that exact text. Otherwise use only the immediately preceding assistant response; never search older assistant responses or combine text from multiple responses. If neither source is available or the boundary is ambiguous, ask the user to provide or paste the exact source instead of choosing one. This source-selection rule is conversational and does not require runtime-specific previous-message machinery.

1. Confirm that the source is clearly bounded text pasted in the request or the immediately preceding assistant response. Extract a preservation ledger before rewriting:
   - facts and decisions;
   - uncertainty, qualifications, and unresolved questions;
   - exact commands, identifiers, links, quoted text, warnings, and code;
   - billing, authentication, authority, and safety language.
2. Rewrite the source in plain English. Simplify sentence structure and explain necessary technical terms, but keep exact searchable terms when replacing them would reduce precision.
3. Compare the candidate with the source ledger. Never invent facts or omit decisions. Never weaken qualifications, broaden permission, soften warnings, or change authority and safety boundaries.
4. Save the exact candidate as UTF-8 and run the separately installed `writing-check` on that candidate:

   ```bash
   uv run --script <writing-check-skill-dir>/scripts/writing_check.py \
     --profile user-facing-response --json <candidate.md>
   ```

5. Verify that the returned source text and `source.sha256` identify the exact candidate. Treat every Vale finding and readability value as advisory evidence, not a gate, score, factual judgment, or authorization to edit protected content.
6. For each finding, either make a semantics-preserving fix when independently justified or retain the text as an exact term, quote, required text, or safety/authority constraint. No finding requires an edit. Discard dispositions whenever the candidate changes.
7. When a `normal` readability sample is below FRE 55 or above FK 10, the observation may scope an optional opportunity for no more than three focused revisions while the preservation comparison still passes. Re-run the source-bound check after any revision. Do not revise merely to target a metric, and do not apply this opportunity to `small_sample`, `insufficient_sample`, `composition_limited`, `disabled`, `unavailable`, or `execution_error` states. A threshold never requires an edit or controls whether the response is returned or considered ready.
8. Return the rewritten response even when advisory findings or readability observations remain. Mention unavailable checker evidence or a preserved constraint briefly when it materially explains the result; never present readability as readiness.

If `writing-check` or Vale is missing, complete the preservation-checked rewrite, report the advisory check as unavailable, and do not substitute another linter or claim a clean result.

## Ownership boundary

Preserve the domain owner's structure when it carries meaning. Never let conversational polish override exact commands, identifiers, links, warnings, code, user intent, factual uncertainty, or release and approval authority. For a requested personal voice, use an explicitly configured external owner only when available; otherwise preserve the user's wording and use neutral prose rather than imitating a voice.
