---
name: research
description: Deep codebase research with an anti-hallucination protocol for verified, citation-backed findings. It should be used whenever investigation materially improves the requested outcome, especially when comparison, explanation, or unfamiliar code/system understanding is substantial. When another workflow owns the final deliverable, keep it primary and scope research to its evidence needs rather than automatically switching to a standalone research package.
---

## Portable execution

Use only available tools and authorized sources. Named research, web lookup,
planning and presentation helpers are optional integrations, not prerequisites.
When unavailable, investigate and synthesize directly with the available tools;
report missing evidence or procedures rather than inventing access or results.
Delegate only when the host supports it and the task authorizes delegation;
otherwise research inline. CLI and source-path examples illustrate methods,
not installed commands or permission to access a private repository. Adapt to
available source readers and cite the actual evidence. No model, provider,
account configuration, persistent destination or implementation permission is
selected by this package. Blindspot remains experimental.


# /research

Investigate a PR, branch, codebase area, or technical concept. Produce verified, citation-backed findings with no hallucination.

## When to Use

- Investigating a PR or branch someone else wrote
- Understanding an unfamiliar codebase area
- Scoping a technical decision with specific code evidence
- Any time investigation, comparison, or explanation is the requested product and factual accuracy matters more than speed

Research may support any task when verified investigation materially improves the result. If another workflow owns the requested deliverable, keep it primary and use as much research depth as the evidence burden requires. Code review, plan validation, ingestion, and handoff verification are examples, not restrictions; use the full research workflow whenever investigation itself becomes a substantial part of the outcome.

## Ownership and Destination Adapters

`research` owns the portable evidence, source-verification, and
anti-hallucination protocol for substantial code, system, and cross-source
investigations, along with selection of their final research artifacts.
`openai-web-research` remains independently callable for a quick cited
public-web lookup. When current web sources contribute to a broader
investigation, it supplies source acquisition while `research` owns the
investigation and outcome.

A destination adapter such as `vault-research`:

- may add destination-specific context, including related notes or local
  indexes;
- may propose whether and where to persist a likely reusable result;
- may hand an evidenced result to a narrower downstream deliverable workflow.

It must not copy or redefine the investigation or anti-hallucination protocol.
It must not force Markdown, HTML, or another artifact solely because the
adapter was invoked. Destination context is input evidence, not presumed truth,
and remains subject to the same source checks.

When the user explicitly requests a destination-aware workflow, keep the
adapter as the primary workflow and use `research` for its evidence pass. When
no destination behavior is requested, use `research` directly and do not
create destination artifacts. A reuse judgment is proposal evidence, not write
consent: persist only when the user explicitly requested the write or approves
the proposed target.

## Instructions

### 1. Gather Context

Infer from the conversation what to research. Identify:

- **Target**: PR URL, branch name, file path, or concept
- **Repo**: Which repository (infer from conversation or current working directory)
- **Branch**: Default branch unless specified
- **Motivation**: Why does the user care? What decision does this inform?

If any of these are unclear, ask upfront — one round of clarification, not a questionnaire:

```
Before I dig in:
- [specific unclear thing]?
- [other specific unclear thing]?
```

### 2. Research

Load `references/anti-hallucination.md` and follow its three constraints throughout.

Investigate inline. When the host supports delegation and the task authorizes it,
a research agent can help with the following evidence pass:

1. **Pull metadata** — PR title/body/files if it's a PR, README/AGENTS.md if it's a codebase area
2. **Read the code** — diffs, key files, architecture. Follow the call chain, don't stop at the surface.
3. **Trace the flow** — for systems work, trace data/control flow end-to-end. Name every file and function.
4. **Flag unknowns** — anything that can't be verified from the code gets marked explicitly.

Verify the premises a conclusion depends on. When a recommendation rests on a factual claim — a quantity, how code or a system behaves, an existing convention, what a source actually says — check it against the cheapest real evidence (a query, the code, existing docs or measurements, a primary source) before building on it; label anything unchecked as an assumption.

Recommend the simplest option that fits existing conventions and the verified constraints. For each added mechanism, name the constraint that requires it; if none, drop it.

### 3. Checkpoint Before Building

When the request mixes research with implementation or worker fan-out, keep research bounded and emit an evidence checkpoint before the first implementation edit or implementation-worker delegation:

- verified facts with citations;
- inferences and material unknowns;
- the decision the evidence supports;
- options considered and why they were rejected;
- the smallest proposed implementation slice and owning files/modules;
- validation and stop conditions.

Proceed only when must-have claims for the slice are supported and remaining unknowns are non-blocking and reversible. Otherwise narrow, clarify, or stop. Do not let research and implementation silently co-evolve through repeated worker retries or architectural reversals.

### 4. Select Deliverables

Always provide a concise inline decision summary. For a substantial conversational
explanation or recommendation, apply `user-facing-response` in normal mode only after
citations, uncertainty, and the supported decision are fixed. If
`user-facing-response` is unavailable, keep this evidence contract and draft the inline
summary directly without invoking Vale by default. Select additional artifacts
independently from the user's decision need:

- **Markdown report** — create when requested, when detailed evidence will be reused, or when the source trail is too large for a scannable inline answer.
- **HTML explainer** — create when explicitly requested or when a visual/shareable artifact adds distinct value for a complex system or multi-stakeholder decision.
- **Full bundle** — create only when inline, Markdown, and HTML each earn distinct utility.

Do not ask the user to choose when the request makes the artifact need obvious. State selected artifacts and the reason briefly. Artifact selection must never weaken citation, quote-before-analysis, source tracing, or explicit uncertainty.

### 5. Connect

After presenting findings, briefly note:
- How this connects to the user's current work (if context is available)
- Questions the user should ask the author
- Anything that looks wrong, incomplete, or worth flagging

## Anti-Hallucination Protocol

See `references/anti-hallucination.md` for the full protocol. The three rules:

1. **Allow "I don't know"** — don't fill gaps with plausible fiction
2. **Cite everything** — file:line for code claims, PR diff lines for changes
3. **Quote before analyzing** — read the code, quote it, then explain

These constraints are non-negotiable in research mode.

## Notes

- For PRs: use `gh pr view` and `gh pr diff` for metadata and diffs
- For branches: check out or read files directly from the branch
- Keep the inline summary scannable — the user wants to decide quickly if they need the full report
- The HTML explainer is the shareable artifact — make it self-contained and visually clear
