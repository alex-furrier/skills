---
name: anti-llm-writer
description: 'Rewrite text to reduce recognizable LLM-writing tropes while preserving clarity, useful structure, and intended meaning. Use when the user asks to "de-llm this," "make this sound less AI-written," "remove LLM vibe," "clean up the slop," or otherwise make prose less synthetic.'
---

# Anti-LLM Writer

## Use this to remove synthetic tropes, not clarity

Revise prose that is generic, inflated, vague, or formulaic while keeping what makes it useful: clear structure, technical precision, and the author’s intended meaning. Do not use this for formal corporate or intentionally templated prose, faithful proofreading, factual-accuracy work, or text that is already precise and human-sounding.

## Happy path

1. Read the whole text for intent and domain. Identify trope categories and severity: low, medium, or high.
2. In `auto` mode, choose the lightest useful edit: normally `regular`; use `de-llm` only when trope density is clearly high.
3. Rewrite with the minimum force needed. Preserve helpful headings, bullets, comparisons, technical organization, and nuanced claims.
4. Return the revised text, requested and selected mode, a one- or two-sentence intensity rationale, and the main trope categories reduced.
5. Scan the result for `my read is` in any casing and replace it with a direct claim or specific uncertainty.

Inputs: required `text`; optional `mode` (`auto | regular | de-llm`, default `auto`) and `preserve_voice` (`true | false`, default `true`).

## Pick the edit intensity

- **`regular`:** light-to-moderate cleanup for mostly good prose with a few inflated words, generic transitions, template cadence, or excess polish. Keep most structure and sentence shapes.
- **`de-llm`:** deeper rewrite for strongly synthetic prose: generic, low-information, repetitive, significance-signaling, or polished without grounding. Cut inflated framing, replace abstractions with concrete claims, and remove filler while preserving meaning.
- **`auto`:** do not escalate because text has headings, bullets, short sections, concise summaries, or parallel formatting. Escalate for vagueness, inflation, filler, and template rhetoric.

## What to look for

Common targets are unsupported importance claims; vague synthesis; unnamed consensus; promotional diction; “not just X, but Y” contrasts; rule-of-three cadence; decorative synonym rotation; filler conclusions; abstraction overload; and formatting that does not improve reading. Replace them with concrete actors, actions, constraints, consequences, and useful examples. Keep a broad term when it is exact.

See [rewrite-reference.md](references/rewrite-reference.md) for the detailed prompts and examples.

## Evidence and preservation boundaries

Do not make prose worse, flatten technical nuance, remove useful organization, replace every bullet with a paragraph, or inject a quirky voice that was not present. Preserve the author's meaning, qualifications, warnings, factual and contractual claims, and safety, authentication, and authority boundaries. Leave machine-consumed syntax and owner-marked literal text intact; do not treat ordinary prose as immutable. A checker suggestion never authorizes a factual or constraint-changing edit.

## Response format

```markdown
### Revised text
[final rewritten text]

### Mode
- requested: `auto` / `regular` / `de-llm`
- selected: `regular` / `de-llm`

### Why this mode
[one or two sentences]

### Main reductions
- [trope category]
```

One-line standard: choose the lightest edit that removes LLM-shaped writing without damaging the communication.
