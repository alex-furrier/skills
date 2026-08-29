---
name: anti-llm-writer
description: 'Rewrite text to reduce recognizable LLM-writing tropes while preserving clarity, useful structure, and intended meaning. Use when the user asks to "de-llm this," "make this sound less AI-written," "remove LLM vibe," "clean up the slop," or otherwise make prose less synthetic.'
---

# Anti-LLM Writer

## Purpose

Revise prose that sounds statistically generic, inflated, vague, or formulaic in common LLM ways, while preserving what is actually good about clear writing.

This skill is for users who want text to sound less synthetic without forcing it into rambling, muddy, or structureless prose.

## Core Doctrine

Preserve clarity. Remove tropes.

Do not confuse anti-LLM writing with:
- long dense paragraphs
- lower readability
- fake informality
- removing headings or bullets just because they are structured
- "humanizing" text by making it worse

The goal is not to make prose messier.
The goal is to make it more specific, restrained, direct, and real.

## What This Skill Does

This skill mainly removes:
- significance inflation
- vague synthesis
- generic "broader landscape" phrasing
- repetitive rhetorical templates
- over-smoothed cadence
- filler conclusions
- polished-but-empty promotional language
- low-information sentences that sound important but say little

It preserves:
- clarity
- useful headings
- useful bullets
- concise sections
- technical organization
- comparison structure when it genuinely helps

## When To Use

Use this skill when the user says things like:
- Make this sound less AI-written
- Remove the LLM vibe
- De-LLM this
- Clean this up but do not overdo it
- Keep the structure, lose the slop
- Rewrite this so it sounds more human
- Make this more concrete and less generic

## When Not To Use

Do not use this skill when:
- the user wants intentionally formal corporate prose
- the user wants marketing copy with polished uplift language
- the user wants a faithful proofread only
- the text is already precise and human-sounding
- the main problem is factual accuracy rather than style
- the user explicitly wants a highly templated format

## Inputs

### Required
- `text`: text to revise

### Optional
- `mode`: `auto | regular | de-llm`
  - default: `auto`
- `preserve_voice`: `true | false`
  - default: `true`

## Outputs

Return:
1. revised text
2. effective mode used
3. short rationale for edit intensity
4. concise changelog of the main trope categories reduced

## Modes

### `auto` (default)

Choose the lightest edit that meaningfully improves the text.

`auto` should infer:
- whether to use `regular` or `de-llm`
- how aggressive to be
- whether structure is helping or hurting
- how much of the original voice to preserve

Default bias:
- prefer `regular`
- escalate to `de-llm` only when trope density is clearly high

### `regular`

Light-to-moderate cleanup.

Use when the text is mostly good but has:
- some inflated wording
- some generic transitions
- mild template cadence
- too much polish or abstraction

Behavior:
- keep structure
- keep most sentence shapes
- tighten vague claims
- remove obvious filler
- reduce rhetorical autopilot

### `de-llm`

Aggressive trope removal.

Use when the text is strongly synthetic:
- highly generic
- low information density
- repetitive contrast structures
- importance-signaling without evidence
- very smooth but not very grounded

Behavior:
- rewrite more deeply
- cut inflated framing hard
- replace abstractions with concrete claims
- simplify rhythm and diction
- remove filler conclusions and empty synthesis
- preserve meaning

## Auto Selection Heuristics

### Choose `regular` if:
- the text is already clear and mostly specific
- structure is helping
- only a few sentences feel synthetic
- the writing has some personal or domain-grounded voice
- stronger edits would flatten it

### Choose `de-llm` if:
- many sentences are generic but polished
- significance language exceeds substance
- claims are vague or weakly attributed
- the prose repeatedly uses stock rhetorical patterns
- the writing sounds "complete" without being concrete
- multiple paragraphs could be cut with little information loss

### Critical Guardrail

Do not escalate to `de-llm` just because the text has:
- headings
- bullets
- short sections
- concise summaries
- parallel formatting

Those are often signs of good writing.

Escalate because of vagueness, inflation, filler, and template rhetoric.

## Detection Targets

### 1. Significance Inflation
Examples:
- a major step forward
- highlights the growing importance of
- underscores the significance of
- reflects a broader shift
- plays a key role in shaping

Preferred fix:
Say what changed, for whom, and why it matters concretely.

### 2. Vague Synthesis Masquerading as Insight
Examples:
- this raises important questions
- it reflects broader tensions
- it sits at the intersection of
- this illustrates the complexity of the issue

Preferred fix:
Name the actual tension, tradeoff, or consequence.

### 3. Generic Attribution or Consensus Language
Examples:
- widely regarded
- many believe
- critics have noted
- has drawn attention

Preferred fix:
Use specific actors or remove the claim.

### 4. Promotional / Polished-Neutral Diction
Examples:
- robust
- seamless
- powerful
- transformative
- innovative
- comprehensive

Preferred fix:
Describe what the thing does.

### 5. Template Contrast Patterns
Examples:
- not just X, but Y
- more than X, it is Y
- not merely X; it is Y

Preferred fix:
State the point directly.

### 6. Rule-of-Three Cadence
Examples:
- clarity, consistency, and scalability
- faster, simpler, and more reliable

Preferred fix:
Keep only when all items are genuinely useful.

### 7. Elegant Variation
Examples:
Rotating synonyms just to avoid repetition.

Preferred fix:
Use the plainest accurate term consistently.

### 8. Filler Conclusions
Examples:
- ultimately
- in conclusion
- looking ahead
- the future remains to be seen
- as the landscape continues to evolve

Preferred fix:
Cut unless the sentence adds a real takeaway.

### 9. Abstraction Overload
Examples:
Too many nouns like:
- framework
- landscape
- evolution
- capability
- paradigm
- approach
- implications

Preferred fix:
Prefer actors, actions, and concrete effects.

### 10. Formatting Artifacts
Potential signs:
- bold overuse
- awkward mini-tables that do not help
- bullets that are really chopped paragraphs
- inline headers everywhere
- em-dash overuse

Preferred fix:
Keep formatting only when it improves reading.

### 11. Disallowed Personal Phrases

Disallow "my read is" in any casing. Rewrite it as a direct claim or name the specific uncertainty instead.

## Rewrite Rules

### Always
- preserve factual meaning
- preserve useful structure
- prefer concrete nouns and verbs
- cut low-information sentences
- keep the prose readable
- preserve technical precision when needed
- favor directness over rhetorical flourish
- scan the final text for disallowed personal phrases

### Usually
- replace generic importance language with specifics
- compress repetitive transitions
- remove stock conclusions
- simplify over-balanced sentences
- reduce adjective density

### Never
- make prose sloppy on purpose
- destroy helpful organization
- flatten technical nuance
- replace all bullets with paragraphs
- remove structure just to seem human
- inject quirky voice unless the source already has one

## Domain Guidance

### Technical Writing
Preserve: headings, bullets, interface descriptions, state transitions, comparison tables when genuinely useful
Reduce: inflated framing, vague strategic importance, conclusion filler, grand abstractions

### Internal Memo
Preserve: concise sections, action-oriented bullets, recommendation structure
Reduce: over-sanitized language, empty synthesis, jargon padding

### Analytical / Academic
Preserve: explicit structure, caveats, careful reasoning
Reduce: faux-scholarly vagueness, "raises important questions" filler, ornamental abstraction

### Marketing-ish Source Text
Preserve: intended persuasive function if needed
Reduce: hype language, claims without specifics, generic adjective stacking

## Process

1. Read the whole text for intent and domain.
2. Detect trope categories.
3. Estimate severity: low, medium, or high.
4. If mode is `auto`, choose `regular` or `de-llm`.
5. Rewrite with the minimum force needed.
6. Preserve structure unless structure itself is part of the problem.
7. Return revised text plus a short note on what changed.

## Response Format

### Revised text
[final rewritten text]

### Mode
- requested: `auto` / `regular` / `de-llm`
- selected: `regular` / `de-llm`

### Why this mode
1–2 sentences explaining the choice.

### Main reductions
- significance inflation
- vague synthesis
- template contrast patterns
- filler conclusion
- promotional diction

## One-Line Standard

Choose the lightest edit that removes the LLM-shaped parts without damaging the communication.
