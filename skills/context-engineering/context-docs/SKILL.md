---
name: context-docs
description: "Opt-in workflow for structured docs directories, including architecture, reference, project-evolution, indexes, and consolidation. Use when context-improve receives --docs, a user requests context-docs, or complete-picture backfill proposes documentation owned by context-docs."
---

> **Opt-in.** This skill is not part of the default `context-improve` flow.
> Run `context-docs` explicitly when you want taxonomy-structured `docs/`,
> or use the `--docs` option with `context-improve` to include it.
>
> Use this skill when a module needs structured documentation beyond its
> agent-context file. `context-agents-md` owns AGENTS.md generation and updates.

**Watermark**: When the target uses YAML indexing frontmatter, generated docs
include `generated-by` and `last-updated` there. Otherwise omit both rather than
introducing a metadata convention.
Portable catalog release: `safurrier-skills`; its Context CLI, `uv`, and plugin-local `cli/` project are required dependencies.

## Portable deterministic evidence

The Context CLI and `uv` are required plugin dependencies. Install the complete Context plugin, including `cli/`; do not copy a Context skill alone. Run `context-engineering ...`. If `uv`, the package, or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Documentation Workflow

Use this opt-in skill for structured architecture, reference, evolution, and
docs-tree maintenance. It owns docs structure and content; `context-agents-md`
owns AGENTS.md generation and updates.

## Activation and mode

Use **analyze** to assess a documentation need, **quickstart** to bootstrap
concise explanation and reference pages, **update** to sync existing docs after
code changes, or **consolidate** to inventory and tidy scattered material.

When no mode is named, choose **update** for existing docs with recent changes,
**quickstart** when the target has no docs, **analyze** for planning or
assessment, and **consolidate** for accumulated material that needs triage. Ask
when that evidence is unclear.

All modes finish with deterministic verification.

Route onboarding walkthroughs and getting-started requests to the repository
README or its established onboarding surface. They may be paired with durable
context docs, but quickstart does not generate a tutorial.

Classify content by reader intent before placing it. The table and placement
rules are in `references/docs-structure.md`.

## Historical proposal intake

Accept a complete-picture `context-backfill` report as evidence input, not as a
document draft or write authority. Recheck each proposed current architecture
claim against the named cutoff or current source before applying it.

- Own architecture, reference, project-evolution, and docs index files.
- Keep architecture focused on current structure and project evolution focused
  on evidenced phases, supersession, and retained tradeoffs.
- Retain immutable provenance for historical assertions in project-evolution
  material.
- Route SPEC and ADR application to `context-contracts`.
- Return the combined diff to `context-review`; do not duplicate backfill's
  claim inventory inside every doc.

---

## Verification

All modes end with deterministic verification through the required catalog CLI:

```bash
context-engineering frontmatter <target-repo-root>
context-engineering references <target-repo-root>
context-engineering antipatterns <target-repo-root>
```

`context-engineering antipatterns` reports structural and maintenance signals;
review its findings as advisory. The bundled `scripts/docs_verify.py` is a
compatibility renderer for the same frontmatter and reference checks and exits
nonzero when copied without the full catalog. Do not replace an unavailable CLI
with manual inspection; install the required dependency and rerun the command.

See `references/deterministic-doc-tests.md` for pytest-based test patterns that repos can adopt.

After those factual and structural checks, run the separately installed
`writing-check` skill on the exact documentation candidate:

- use `technical-doc-explanatory` for explanations and prose-heavy procedures;
- use `technical-doc-reference` for APIs, configuration, schemas, command
  references, and identifier-dense pages;
- do not infer document intent from a readability score;
- keep checker findings, composition limits, and readability advisory and
  separate from deterministic link, frontmatter, index, and structure failures;
- if writing-check is unavailable or errors, report that state rather than a
  clean result.

Both technical profiles use the broad reviewed portable policy plus narrow
mechanical host terminology. They become normal at 300 included prose words and
8 sentences and use private FRE 55 / FK 10 observations. Reference docs can be
`composition_limited` when tables and fragments dominate. In quickstart or
update mode, fix or explicitly disposition every finding against the exact
`source.sha256`; audit-only modes report the queue without editing. Complete
accounting remains advisory and is not a quality, readiness, or publication
gate.

Context Docs still owns taxonomy, current architecture and reference facts,
links, indexes, and deterministic verification. Preserve exact identifiers,
commands, links, machine blocks, safety/security/authentication/billing facts,
and authority language through domain-owner judgment. Require independent
semantic-preservation review for broad existing-prose rewrites and for changes
to architecture claims, procedures, warnings, migration behavior, or authority
boundaries. Audit-only runs do not edit files.

---

## Mode: Analyze

**Purpose**: Audit existing documentation and create a documentation plan.

**Use when**: Starting fresh, assessing documentation needs, planning what to write.

**Process**:
1. Study any reference documentation as exemplars
2. Scan existing docs (e.g., `/docs` directory)
3. Identify gaps, outdated content, or temporary documentation
4. Create a documentation plan

**Output**: For each proposed document:
- Document title and output location
- Table of contents / structured outline
- 100-200 word writing sample demonstrating style

**Validation checklist** (verify before finishing):
- [ ] Every proposed doc has title, location, TOC, writing sample, priority, and effort estimate
- [ ] Commands in writing samples are annotated as verified (confirmed from source) or unverified
- [ ] No speculative content; omit sections that code does not verify rather than guessing
- [ ] Output follows the structured plan format from `references/analyze.md`

**Detailed instructions**: Load `references/analyze.md`

---

## Mode: Quickstart

**Purpose**: Bootstrap concise, durable explanation and reference docs for a module.

**Use when**: A module needs documentation from scratch or comprehensive refresh.

**Inputs** (gather from user or infer):
- `feature_dir`: Repo-relative path to the module
- `tech_stack`: Languages, frameworks, services
- `scope`: What modules are covered
- `known_docs`: Any existing related docs

**Output location**: `<feature_dir>/docs/`

**Generated files** (placed in intent folders):
```
explanation/architecture.md # Structure with diagrams (≤5 diagrams total)
reference/<topic>.md        # Current commands, APIs, schemas, or types
reference/data.md           # Tables, cache keys, invariants (only if applicable)
```

Use `reference/cli.md` for command-driven modules and
`reference/interfaces.md` for API- or schema-driven modules. Prefer an existing
repository naming convention when one is already established.

**Not generated:**
- `tutorials/` — onboarding tours, exercises, and learning sequences are deliberately
  out of scope. `docs/` is for durable reference material, not onboarding walkthroughs.
  Use repo README or a separate onboarding doc for that.
- `how-to/*.md` — per P12, procedural workflows become skills at
  `.agents/skills/<name>/SKILL.md`. Surface them as skill proposals in the
  report instead of writing markdown. See "Skill Proposals" section below.

**Diagram rules**:
- Prefer Mermaid `flowchart LR`
- ≤10 nodes per diagram, ≤5 diagrams total
- No parentheses `()` in node text

**Detailed instructions**: Load `references/quickstart.md`

---

## Mode: Update

**Purpose**: Sync documentation with code changes.

**Use when**: Code has changed and docs may be stale.

**Auto-detection** (in order):
1. Uncommitted changes in working directory
2. Current branch vs main/master
3. Last 10 commits on current branch
4. Last 7 days of commits (fallback)

**Change categories**:
- 🔴 **Breaking**: API changes, removed features, changed behaviors
- 🟡 **Feature**: New functionality, endpoints, options
- 🟢 **Enhancement**: Performance, UI/UX improvements
- **Fix**: Bug fixes affecting documented behavior

**Sub-modes**:
- `PLAN` (default): Present update report, ask which to proceed with
- `AUTO`: Execute critical and important updates automatically

**Output format**:
```markdown
## Documentation Update Report

### Summary
- X files need updates
- Y new documents recommended
- Z deprecated sections to remove

### Priority Actions
#### 🔴 Critical Updates
#### 🟡 Important Updates
#### 🟢 Minor Updates

### Detailed Changes
[File-by-file instructions]
```

**Detailed instructions**: Load `references/update.md`

---

## Mode: Consolidate

**Purpose**: Inventory all docs in a repo, classify each file, and produce a manifest to clean up stale, scattered, or misplaced content.

**Use when**: Docs have accumulated over time and need triage — finished
migration plans, redundant references, or gaps with no doc. Route AGENTS.md
implementation work to `context-agents-md`.

**Sub-modes**:
- `PLAN` (default): Produce inventory report and manifest; present before touching any files
- `AUTO`: Execute manifest after showing it

**Classification**: First classify each file by doc type (tutorial/how-to/explanation/reference) and audience (agent/human). Then derive the action:
- **Keep**: Accurate reference docs, architecture docs, how-to guides still actively used
- **Archive** → `docs/_archive/`: Completed migration plans, one-time runbooks for finished work, superseded content
- **Move**: Misplaced documentation between owned docs surfaces. Refer
  AGENTS.md implementation or extraction proposals to `context-agents-md`.
- **Create**: Identified gaps (e.g., no routing index, missing reference doc for a configured tool)
- **Rename**: Naming inconsistencies vs. derived conventions

**Output format**:
```markdown
## Consolidation Report

### Inventory
- X files in docs/
- Y AGENTS.md files with proposals routed to `context-agents-md`
- Z root .md files

### Manifest
#### Keep
- docs/architecture.md — accurate architecture reference
#### Archive → docs/_archive/
- docs/migration-plan-2024.md — migration complete, superseded
#### Move
- context-agents-md proposal: route an AGENTS.md section to docs/editor-reference.md
#### Create
- docs/AGENTS.md — routing index for docs/

### Actions pending: N
```

**Detailed instructions**: Load `references/consolidate.md`

---

## Skill Proposals (replaces how-to generation)

Per P12, how-to content routes to skills, not markdown. In any mode, when
procedural content is identified, emit it as a skill proposal in the report
instead of writing a `docs/how-to/*.md` file.

### Decision framework

A workflow is a skill candidate when ALL are true:
1. Repeatable procedure (agent would execute > once)
2. Concrete commands (not high-level guidance)
3. Agent-executable (no cross-team coordination required)
4. Decision-making involved (branches/selection, not a single linear recipe)

If 1-3 are true but there's no decision-making, it's still a skill candidate —
but a simple one. If only 1-2 are true, it's reference material, not a skill.

If content fits how-to *format* but fails the criteria (one-time migration or
cross-team rollout), route durable rationale to `docs/explanation/` and keep
temporary execution state in the owning plan or task system. Do not create a
generated tutorial as a fallback.

### Proposal format (in the report)

```markdown
## Skill Proposals

### <kebab-case-skill-name>
- **Source**: <path to how-to content that inspired this>
- **Trigger**: <when should this skill activate?>
- **Procedure summary**: <2-3 sentence description>
- **Install location**: `.agents/skills/<name>/SKILL.md`

Rationale: <why this passed the P12 criteria>
```

Do NOT auto-create the skill files. Propose, let the user decide.

### Install convention

If the user approves a proposal, follow
[`references/skill-install-convention.md`](references/skill-install-convention.md):

1. Discover and preserve the target repository's existing skill directory and
   linking convention. If none exists, propose `.agents/skills/<name>/` without
   creating compatibility symlinks implicitly.
2. Create `<skill-dir>/SKILL.md` with valid `name` and `description` frontmatter,
   the approved trigger, procedure, boundaries, and validation steps. Use an
   installed skill-authoring workflow when available; otherwise follow the
   portable requirements in the linked convention.
3. Validate with `context-engineering skills <skill-dir>`. If the required CLI cannot run, stop and report the missing dependency; do not replace plugin validation with direct local checks.

---

## Universal Guidelines

See `references/principles.md` for the full set of documentation principles that guide all modes.

**Writing style**:
- Concise, factual, imperative voice
- Prefer examples over prose
- Every documented element should serve a purpose
- Good docs are discoverable, actionable, maintenance-friendly

**Frontmatter**: Treat each `docs/` directory as an independently governed docs
tree. First inspect content files owned by the target tree, excluding content
beneath any nested `docs/` tree. If any establish YAML indexing frontmatter,
preserve that convention on created or touched content files in that tree and
validate it consistently. If none do, emit plain Markdown. A sibling or parent
docs tree cannot establish the convention for the target. AGENTS.md files are
routing indexes and never require frontmatter.

When the convention exists, use this simplified shape unless the repository
defines a different schema:
```yaml
---
id: kebab-case-id
title: Human Title
description: >
  1-2 sentences for routing.
index:
  - id: section-slug
---
```

**Indexes**: All modes that create or move docs should create or update two index files:
- `docs/README.md` -- human reading order, with explanation before reference for
  newly bootstrapped trees; preserve and index established tutorial/how-to docs
- `docs/AGENTS.md` -- agent routing by doc type (no frontmatter — routing index only)

See `references/docs-structure.md` for index format and scaling rules.

**Guardrails**:
- Don't speculate; omit what code does not verify rather than guessing
- Ask before running long-lived or side-effecting processes
- Verify commands work before documenting them
- Keep each page to two screens or fewer; link deeper where necessary
- Label local wrappers, private CLIs, absolute home paths, credential profiles,
  and user-specific automation as environment-specific. Include the dependency,
  installation source, vanilla/portable fallback (or say none exists), and
  missing-tool behavior. Put `<!-- environment-specific-dependencies:v1 -->`
  immediately before governed dependency headings so the contract is
  inventoryable. Do not make a personal tool a universal prerequisite.

**Scope boundary**: This skill owns docs/ structure, indexes, and content file management.
AGENTS.md files (root and nested) are owned by `context-agents-md`. If both
skills are being used, this skill handles docs/ operations while that owner
handles AGENTS.md routing and implementation.

**Final editorial pass** (always do):
- Remove unverified or speculative details
- Dedupe redundant content across files
- Remove verbose explanations that don't change decisions or actions
