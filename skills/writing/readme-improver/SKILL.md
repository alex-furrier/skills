---
name: readme-improver
description: "Create, audit, and update README.md files using a reader-journey structure, code-backed discovery, verified commands, and anti-slop editing. Use when writing a new README, improving an existing README, grading README quality, or when the user mentions README drift, hodgepodge docs, or AI-vibey documentation."
---

# README Improver

Improve READMEs by turning repo facts into a guided reader journey. Prefer plain,
code-backed documentation over feature inventory, marketing language, or generic
AI prose.

## Modes

Choose one mode before editing:

- **Init**: Create `README.md` when it is missing or intentionally being replaced
  from scratch.
- **Update**: Improve an existing `README.md` while preserving accurate useful
  content and repo-specific voice.
- **Audit**: Grade a README and produce findings without editing unless the user
  asks for changes.

When the user does not specify a mode, infer it from the repo state: missing
README means Init, existing README means Update, review-only wording means Audit.

## Core rule

Treat a README as a journey, not an inventory. Teach the reader in this order:

1. Orient them: what this is, who it is for, and why it exists.
2. Get them to a first useful result with the shortest safe path.
3. Explain the mental model, repo shape, and tradeoffs needed to keep going.
4. Move detailed commands, config, options, troubleshooting, and contributing notes into reference sections or deeper docs.

These are internal planning stages, not public labels. Do **not** use workshop terminology such as `First Contact`, `Black Triangle`, `Hairball`, or similar journey labels as generated README headings or prose unless the existing project already uses them as real product/domain terms. Translate the structure into normal reader-facing headings such as `Quick start`, `How it works`, `Common workflows`, `Configuration`, or repo-specific equivalents.

Load [references/readme-workflow.md](references/readme-workflow.md) for the full
workflow and [references/readme-rubric.md](references/readme-rubric.md) when
grading or running trials.

## Discovery before writing

Do enough discovery to avoid inventing docs:

1. Identify the README scope from the README directory. In a monorepo, a nested
   README documents that subtree unless the user says otherwise.
2. Read repo guidance first: nearest `AGENTS.md`, `CLAUDE.md`, existing docs
   index, package metadata, task files, and current README if present.
3. Detect the actual toolchain from files such as `.mise.toml`, `justfile`,
   `Makefile`, `pyproject.toml`, `Cargo.toml`, `package.json`, lockfiles,
   `uv.lock`, `go.mod`, and CI workflows.
4. Extract examples from real sources: tests, `examples/`, CLI help, docs,
   scripts, or source comments. Mark uncertain examples as uncertain instead of
   presenting them as tested. For YAML/TOML/JSON snippets, say whether they are
   copied from repo docs/fixtures/tests or are minimal illustrative examples. For
   MCP, API, SDK, or CLI-tool examples, compare copied examples against current
   function signatures, schemas, generated help, or tests before keeping them.
5. Verify recommended commands exist. Prefer cheap non-mutating checks such as
   `--help`, task listing, source inspection, or metadata inspection before
   recommending commands. Classify commands as read-only, validation-only,
   mutating local files, host-mutating, or external-service-mutating.
6. Do not infer PyPI, npm, Homebrew, or package-registry availability from package
   metadata alone. Separate source-checkout installs from registry installs and
   label registry commands that were not verified in the README itself, not only
   in the final response.
7. If verification is blocked by trust prompts, missing README package metadata,
   network installs, or unsafe side effects, do not force it. Record the command
   as metadata-backed or unverified and explain why.
8. For Update mode, compare README claims against current repo facts and related
   docs. When README, docs, `AGENTS.md`, tests, and source disagree, prefer
   executable source/tests/CLI help/nearest `AGENTS.md` and flag stale docs.
9. Scan for structural drift: empty headings, duplicate setup paths, stale
   migration notes, template leftovers, version strings that drift, generated
   blocks, and command/reference tables that duplicate deeper docs.

Use parallel discovery when the environment supports it. Otherwise use parallel
tool calls or inspect inline.

## Writing rules

- Lead with what the reader can do, then explain why it matters.
- Keep the fastest safe successful path near the top. For tools that write to
  `$HOME`, install services, publish, deploy, send messages, or touch external
  systems, start with `--help`, `doctor`, `status`, `dry-run`, auth checks, or
  read-only commands before mutating examples. If the first meaningful setup
  command must write local config and has no dry-run, keep it in quick start but
  state the exact path it writes.
- For credentialed CLIs, name required credentials/permissions and include a
  read-only auth or status check before production API examples.
- For setup, daemon, MCP, service, or client-integration repos, include a cheap
  success signal: validation passing, help/version output, health/status check,
  log line, tool-list result, or client-visible confirmation. If a cheap
  read-only command is available, include one tiny expected-output cue or explain
  why no output was captured.
- For multiple primary CLIs/products, add a `Pick your path` section with one
  shortest success path per audience. Put optional companion apps/APIs after the
  primary first success.
- For archive, catalog, or generated-index repos, make the README an index and
  contribution/update guide. Do not force package-style sections.
- Use headings that say the point: `Run the local check` beats `Validation`.
- Include code blocks for commands. Add expected output or a success signal when
  it prevents ambiguity.
- Link to deeper docs instead of copying everything into the README. If command,
  config, API, or tool references duplicate docs, keep a small workflow table and
  link to the reference.
- Use repo-specific wording and tradeoffs. Avoid generic claims that could fit any
  project.
- Keep gotchas actionable: **DO X, NOT Y, BECAUSE Z**.
- Preserve good human-written content, maintainer warnings, and terms of art even
  if the surrounding README needs restructuring. Preserve at least the useful
  sentence, quote, or callout from distinctive sections unless it is inaccurate or
  harmful. Prefer surgical updates when an existing README already has a strong
  journey.
- When `AGENTS.md`, `CLAUDE.md`, or a docs index is the main Init source, extract
  only the reader-facing purpose, shortest path, small repo map, and 3-5 highest
  value invariants. Link the rest.
- Before finalizing Init or Update, verify the scoped `README.md` exists at the
  target path. If Init cannot write it, stop and report blocked instead of
  claiming completion.

## Final writing evidence

After factual discovery, reader-journey repair, command verification, and the
actual draft, identify maintainer-distinctive wording plus exact commands,
identifiers, links, marker blocks, warnings, billing/authentication facts, and
safety or authority language. These remain domain-owner judgments; never change
them merely to satisfy a rule or readability band.

Run `writing-check --profile readme` on the exact candidate. If the checker or
Vale is unavailable, continue only with the authorized README judgment, report
the unavailable state, and do not claim clean evidence or substitute another
linter. Treat its reviewed Google Vale v0.7.1 rules and readability sample as
advisory evidence. The policy excludes the upstream Google word lists and does
not make contextual product substitutions:

- under 100 included prose words or 5 sentences is `insufficient_sample`;
- 100–299 words is normally `small_sample`;
- 300 words and 8 sentences is `normal`, with private FRE 55 / FK 10 targets;
- table- or fragment-heavy READMEs can be `composition_limited` with no target.

Judge each finding against repository truth, technical searchability, and the
reader journey. In Init or Update mode, fix or explicitly disposition every
finding against the exact `source.sha256`. A finding can remain visible while the
owner keeps an exact term, quote, required warning, or distinctive voice. This
accounting is not a quality, readiness, or publication gate. If the source
changes, re-run the check instead of carrying forward a stale digest.

Require an independent semantic-preservation pass when a broad rewrite changes
existing human-authored long-form prose, architecture claims, warnings,
procedures, safety/security/authentication/permissions/billing/legal language,
exact commands, migration behavior, or authority boundaries. Audit mode remains
non-mutating and returns evidence without replacement prose.

## Anti-slop judgment

Review inflated or generic words in context instead of applying an absolute
ban. Remove feature soup before first success, badge theater, decorative emoji,
forced symmetry, fake enthusiasm, generic conclusions, invented examples or
output, unverified install commands, and contradictory setup sections. Keep a
marketing-sounding term when it is technically exact and no clearer wording
preserves the claim.

Keep personality when it is specific and useful. Do not sand every README into a
neutral template.

## Output expectations

For edits, provide:

- Files changed.
- What improved in the journey.
- Top journey gaps found and whether each was fixed, deferred, or intentionally
  left unchanged.
- Commands or facts verified, using labels such as `verified by running`,
  `verified by metadata`, `not run: unsafe/expensive`, `not run: trust required`,
  or `not verified`.
- Useful content preserved from the original README.
- Tradeoffs or sections intentionally moved, shortened, or left alone.

For audits, use the rubric in [references/readme-rubric.md](references/readme-rubric.md)
and report concrete findings with file/section references.