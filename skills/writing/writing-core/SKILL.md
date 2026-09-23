---
name: writing-core
description: Provide lightweight drafting principles for clear, specific, natural technical communication. Use when drafting ordinary documentation, commit copy, comments, status updates, and other prose before a destination owner or advisory checker applies its narrower contract.
---

# Writing Core

## Use this for ordinary technical prose

Write like a trustworthy colleague: lead with the outcome, make the next action clear, and preserve technical meaning. This skill offers drafting guidance only. It does not own repository facts, destination structure, deterministic findings, or publication.

## Happy path

1. State the concrete outcome, behavior, or request before the background.
2. Use specific actors, nouns, examples, and observed effects. Keep exact, searchable, or audience-familiar technical terms; define an unfamiliar term when that is clearer than replacing it.
3. Choose paragraphs and lists for the content. Do not force symmetry, a fixed bullet count, or a rule of three.
4. Keep meaningful uncertainty, limitations, and natural cadence. Do not manufacture roughness to sound human.
5. Verify facts and examples against their owner. Remove filler, feature soup, unsupported emphasis, and conclusions with no decision or action.

Review broad terms such as “robust,” “capability,” and “comprehensive” in context. Replace one only when a more specific phrase preserves the claim; do not use a universal banned-word list.

## Preserve owner-controlled text

Preserve technical meaning, qualifications, warnings, facts, and safety, authentication, contractual, and authority boundaries. Literal bytes matter for machine-consumed syntax and identifiers, policy, configuration, rule, or license integrity, a machine-managed block, or an explicit owner requirement; ordinary prose need not retain its spelling. When using Writing Check, bind findings to the checked candidate and its source digest. A checker suggestion, readability target, or style rule never authorizes a factual or constraint-changing edit.

## Route to the owner

- Follow the target repository’s conventions for commit text. Without a configured external voice owner, preserve the author’s meaning and use neutral imperative prose.
- Use `pr-description` for `Why / What changed / Evidence`, behavioral explanation, and reviewer value.
- Use `readme-improver` for repository truth, reader journey, verified commands, and maintainer content.
- Use `context-docs` for structured architecture and reference documentation.
- Use `user-facing-response` for substantial agent-facing plans, explanations, recommendations, summaries, handoffs, or an explicit plain-English rewrite.
- Use `writing-check` only after a candidate exists, for deterministic advisory evidence. The destination owner judges findings and owns edits.

For a requested personal or organization voice, use a configured external owner when available. Otherwise preserve supplied wording and use neutral prose. If `user-facing-response` is unavailable, continue with this guidance and the destination owner’s contract; do not add Vale to ordinary conversation. GitHub Open PR remains the sole Git/GitHub mutation owner in its publication workflow.

## Final pass

Run the destination’s required writing check when applicable. `no_findings` means only that no configured pattern matched; it does not establish correctness or readiness. For an explicit de-LLM rewrite or synthetic-prose audit, use `anti-llm-writer`. Load [contextual examples](resources/drafting-examples.md) only when a before/after illustration will help.
