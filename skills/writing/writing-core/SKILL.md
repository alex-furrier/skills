---
name: writing-core
description: Provide lightweight drafting principles for clear, specific, natural technical communication. Use when drafting ordinary documentation, commit copy, comments, status updates, and other prose before a destination owner or advisory checker applies its narrower contract.
---

# Writing Core

Write trustworthy prose that sounds like a colleague and preserves technical meaning. This skill supplies drafting principles only. It does not own repository facts, destination structure, deterministic findings, or publication.

## Draft

1. State the concrete outcome, behavior, or request before background.
2. Prefer specific nouns, actors, examples, and observed effects over promotional or abstract language.
3. Use technical terms when they are exact, searchable, or familiar to the audience. Define an unfamiliar term when that helps more than replacing it.
4. Let the content choose paragraph and list shape. Do not force symmetry, a fixed bullet count, or a rule of three.
5. Keep meaningful uncertainty, limitations, and human cadence. Do not manufacture roughness to look human.
6. Preserve exact commands, identifiers, links, quoted text, warnings, billing and authentication facts, safety language, and authority boundaries.

Review inflated language in context rather than applying a universal word ban. Words such as “robust,” “capability,” or “comprehensive” can be vague, but they can also be exact. Replace one only when a more specific phrase preserves the claim. Transitions, personal phrasing, and imperative mood also depend on destination and intent.

## Route ownership

- For commit text, follow the target repository's documented conventions; if no configured external owner is available, preserve the author's intended meaning and use neutral imperative prose.
- Use `pr-description` for `Why / What changed / Evidence`, behavioral explanation, and reviewer value.
- Use `readme-improver` for repository truth, reader journey, verified commands, and maintainer content.
- Use `context-docs` for structured architecture and reference documentation.
- Use `user-facing-response` to shape substantial agent-facing plans, explanations, recommendations, summaries, and handoffs, or to handle an explicit plain-English rewrite.
- For a requested personal or organization-specific voice, use a configured external owner when available; otherwise preserve the supplied wording and use neutral prose.
- Use `writing-check` only for deterministic advisory evidence after a candidate exists.

When `user-facing-response` is unavailable, continue with these drafting principles and the destination owner's contract; do not add Vale to ordinary conversational drafting. A destination owner judges every finding and owns any edit. GitHub Open PR remains the sole Git/GitHub mutation owner in its publication workflow.

## Final pass

- Verify facts and examples against the owning source.
- Remove filler, feature soup, unsupported emphasis, and conclusions that add no decision or action.
- Read for rhythm and ambiguity, not compliance with a fixed personal voice.
- Run the destination's writing check when its owner requires one; `no_findings` means only that no configured pattern matched.

For an explicit de-LLM rewrite or synthetic-prose audit, use `anti-llm-writer`. Do not create a generic docs improver or technical-writing editor around these principles. Load [contextual examples](resources/drafting-examples.md) only when a before/after illustration helps.
