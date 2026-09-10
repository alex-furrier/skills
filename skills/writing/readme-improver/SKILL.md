---
name: readme-improver
description: "Create, audit, and update README.md files using a reader-journey structure, code-backed discovery, verified commands, and anti-slop editing. Use when writing a new README, improving an existing README, grading README quality, or when the user mentions README drift, hodgepodge docs, or AI-vibey documentation."
---

# README Improver

## Purpose

Turn verified repository facts into a reader journey: orient a cold reader, get them to a safe first result, explain the needed mental model, then link to detail. Prefer plain, code-backed documentation over inventories, marketing, and generic AI prose.

## Choose the mode and path

- **Init:** create a missing README or replace it only when explicitly requested.
- **Update:** improve an existing README while preserving accurate, useful content and repository voice.
- **Audit:** grade and report findings without edits.

Infer Init for a missing README, Update for an existing one, and Audit for review-only wording. If ambiguity remains, take the least destructive path and audit first.

For Init/Update:

1. Scope from the README directory: a nested README documents its subtree unless told otherwise.
2. Read local guidance first: nearest `AGENTS.md`, `CLAUDE.md`, docs index, existing README, package/task metadata, and then relevant docs, source, tests, examples, and CLI help.
3. Verify facts before documenting them. Find the actual toolchain from task/package files and CI. Verify recommended commands with cheap, non-mutating evidence where safe; classify each as read-only, validation-only, local-file-mutating, host-mutating, or external-service-mutating.
4. Build the shortest safe first-success path. Lead with what the reader can do. For risky setup, use `--help`, `doctor`, `status`, dry-run, or auth checks first; if setup must write without a dry-run, name the exact path it writes.
5. Explain only the mental model and repo shape needed next. Keep deeper commands, configuration, options, troubleshooting, and contributing detail in references or linked docs.
6. Verify the scoped `README.md` exists before claiming Init is complete.

Load [the full workflow](references/readme-workflow.md) for discovery, structure, and verification detail. Load [the rubric](references/readme-rubric.md) for Audit and trials.

## Evidence boundaries

Extract examples from real tests, examples, CLI help, docs, scripts, or source. Mark uncertain examples as uncertain. Label YAML/TOML/JSON examples as copied or illustrative, and compare MCP/API/SDK/CLI examples with current signatures, schemas, generated help, or tests. Do not infer registry availability from metadata: distinguish source-checkout from registry installs and label unverified registry commands in the README itself.

When a command is blocked by trust prompts, missing metadata, network installs, or unsafe side effects, do not force it. Label it `verified by running`, `verified by metadata`, `not run: unsafe/expensive`, `not run: trust required`, or `not verified`. If README/docs/guidance/source disagree, prefer executable source, tests, CLI help, and nearest `AGENTS.md`; flag stale documentation. Scan for empty headings, duplicate setup, stale migration notes, template leftovers, version drift, generated blocks, and duplicated references.

Keep bytes exact only for a real exact-byte consumer: the candidate supplied to Writing Check and its source digest; policy, config, rule, and license integrity assets; machine-consumed command syntax and identifiers; and text the user or owning contract explicitly marks exact. Preserve the meaning, qualifications, and safety, authentication, authority, factual, and contractual constraints of all other prose. A checker suggestion alone never authorizes a factual or constraint-changing edit.

## Write for the reader

Use point-bearing headings such as `Run the local check`, code blocks for commands, and a success cue when it prevents ambiguity. Include `Pick your path` for multiple primary audiences; put companion apps/APIs after first success. For service, daemon, setup, MCP, or client integration, include a cheap success signal. For archive/catalog/generated-index repositories, make the README an index and update/contribution guide rather than forcing package sections.

Keep repo-specific tradeoffs and actionable **DO X, NOT Y, BECAUSE Z** gotchas. Link out instead of copying long tables or references. Preserve accurate, distinctive maintainer wording, warnings, terms of art, and at least the useful sentence, quote, or callout from distinctive sections unless it is inaccurate or harmful. Do not leak internal planning labels such as `First Contact`, `Black Triangle`, or `Hairball` into public prose unless they are real existing domain terms.

In Update, read once for voice, list journey gaps, and prefer a surgical patch when the README is already strong. Reorder around orientation, first success, mental model, and reference; do not replace it with a generic template. Remove feature soup, badge theater, decorative emoji, forced symmetry, fake enthusiasm, invented examples/output, unverified installs, contradictory setup, and conclusion filler. Keep technically exact terms and useful personality.

## Final evidence

Run `writing-check --profile readme` on the exact Init/Update candidate after factual discovery and drafting. If Vale is unavailable, complete only the authorized README judgment, report `unavailable`, do not substitute another linter, and never claim clean evidence or that a checker ran. Its Google Vale v0.7.1 observations and readability sample are advisory: under 100 included prose words or 5 sentences is `insufficient_sample`; 100–299 is normally `small_sample`; 300 words and 8 sentences is `normal` with private FRE 55 / FK 10 observations; table/fragment-heavy documents may be `composition_limited` with no target.

Judge each finding against repository truth, searchability, and the reader journey. In Init/Update, fix or explicitly disposition each against the exact `source.sha256`; an owner may retain an exact term, quote, warning, required text, or voice. This accounting is never a quality, readiness, or publication gate. Rerun after source changes. A broad rewrite of existing human-authored long-form prose, architecture, warnings, procedures, safety/security/authentication/permissions/billing/legal language, exact commands, migration behavior, or authority boundaries requires an independent semantic-preservation pass. Audit remains non-mutating.

## Return

For edits, report changed files; journey improvements; the top gaps as fixed/deferred/unchanged; verified facts and commands using the labels above; preserved material; and intentional moves, shortening, or tradeoffs. For audits, use the reference rubric and cite concrete file/section evidence without replacement prose.
