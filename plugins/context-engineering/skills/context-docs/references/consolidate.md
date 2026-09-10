# Docs Consolidation Workflow

Detailed instructions for **consolidate** mode.

Inventory all documentation in a repo, derive the structural conventions that already exist bottom-up, classify each file against those conventions, and produce a migration manifest to clean up stale, scattered, or misplaced content — including naming inconsistencies.

## Contents

- [Inputs](#inputs)
- [Inventory](#step-1-inventory)
- [Derive conventions](#step-15-derive-conventions)
- [Classify each file](#step-2-classify-each-file)
- [Build the manifest](#step-3-build-manifest)
- [Execute](#step-4-execute)
- [Report](#step-5-report)
- [Guardrails](#guardrails)

---

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `scope` | Root path to scan | repo root |
| `mode` | `PLAN` or `AUTO` | `PLAN` |

**Always run PLAN first.** Present the manifest before touching any files. Only proceed to execution on confirmation or in AUTO mode.

---

## Step 1: Inventory

Find all documentation files:

```
1. docs/*.md and docs/**/*.md
2. All AGENTS.md files (non-archive, non-vendored)
3. Root-level .md files (README.md, TROUBLESHOOTING.md, etc.)
```

Exclude: `_archive/`, `archive/`, `.git`, `.venv`, `node_modules`, `__pycache__`, vendored plugin directories.

Build an inventory table before doing anything else:

```
| File | Lines | Classification (initial) |
|------|-------|--------------------------|
| docs/architecture.md | 80 | Permanent reference |
| docs/migration-plan-2024.md | 45 | Archive candidate (migration done?) |
| config/editor/AGENTS.md | 120 | Has human-facing content? |
```

---

## Step 1.5: Derive Conventions

Before classifying, observe the naming and organizational patterns that already exist. Derive the standard bottom-up from what's there — don't impose conventions top-down.

### What to look for

**Naming patterns** — what do files named similarly have in common?
- `{tool}-reference.md` → human-facing keyboard/config references
- `{topic}-architecture.md` → system design / cross-cutting design docs
- `tools/{tool}.md` → per-tool setup or usage guides
- `{topic}-onboarding.md`, `{topic}-quickstart.md` → getting-started guides

**Structural patterns** — where does content live?
- `docs/` top-level → cross-cutting references, architecture, guides used daily
- `docs/tools/` → per-tool docs for secondary/utility tools
- Root-level → `README.md`, `TROUBLESHOOTING.md` (operational)
- Module `AGENTS.md` → agent-facing file maps, commands, invariants

**Gaps in the derived standard** — do files exist that violate the pattern?
- A file named `ghostty-shortcuts.md` in a repo where every other tool uses `{tool}-reference.md`
- Tool docs at top-level when similar tools live in `docs/tools/`

### Output

Produce a **Conventions** section as the first block of the manifest:

```
Conventions (Derived)
=====================
Naming:
  Human-facing tool references → docs/{tool}-reference.md
  Per-tool setup docs → docs/tools/{tool}.md
  Architecture docs → docs/{topic}-architecture.md

Structure:
  docs/ top-level — key references, architecture, guides
  docs/tools/ — per-tool docs for secondary tools

Inconsistencies found (→ RENAME in manifest):
  docs/ghostty-shortcuts.md → docs/ghostty-reference.md
```

These inconsistencies become RENAME actions in the manifest.

---

## Step 2: Classify Each File

Classification has two dimensions:

### Dimension 1: Doc Type + Audience

For each file, determine:
- **Doc type**: tutorial, how-to, explanation, or reference. Use the intent classification from `docs-structure.md` (two questions: action/cognition x acquisition/application).
- **Audience**: agent (navigates file maps, runs commands) or human (presses keys, types aliases, configures UI).

### Placement check

Existing repository conventions win. Preserve established tutorial and how-to
trees, but do not create them or move flat files into them. For a flat unmanaged
tree, MOVE actions may place durable system material under `explanation/` and
lookup material under `reference/`. Route reusable procedures to skill
proposals; keep their source file in place until an approved application owns
its removal. Keep onboarding material at its established path and recommend a
README pointer or update rather than creating `tutorials/`.

Also flag individual docs that exceed `README.md` P11
sizing targets (docs files over 500 lines) as needing review or splitting in
the manifest.

### Dimension 2: Action

From the classification above, derive the action for each file:

**Keep**
*Correctly typed, correctly placed. May need frontmatter normalization only
when its independently governed docs tree establishes that convention.*

Signals:
- Architecture docs, system design, data flows
- How-to guides and runbooks that remain relevant
- Tool reference docs (setup, usage, configuration)
- Onboarding guides that reflect current state

**Archive** → `docs/_archive/`
*Content is stale, superseded, or no longer relevant.*

Signals:
- Migration plan for a migration that's complete
- One-time runbook for a setup that no longer exists
- Research or planning docs for a decision that's been made
- Duplicate of content that exists elsewhere in better form

To confirm an archive candidate: check if the work it describes is done (look at git history, check if referenced paths/systems still exist).

**Move**
*Correctly typed, wrong location.*

Apply the **actor test**:
- Human-facing content in AGENTS.md → `docs/{topic}-reference.md`
- Agent-facing content in `docs/` that belongs in a module AGENTS.md

**Create**
*Gap identified -- needed doc doesn't exist.*

Signals:
- `docs/AGENTS.md` index doesn't exist
- `docs/README.md` index doesn't exist (Navigation principle: both indexes are required for every docs/ directory)
- A configured tool has no reference doc (e.g., `config/tmux/` exists but no `docs/tmux-reference.md` and keybindings are buried in AGENTS.md)
- Architecture doc referenced from AGENTS.md doesn't exist

**Rename**
*Correct content, wrong name vs. derived conventions.*

---

## Step 3: Build Manifest

Produce the full manifest before any file operations:

```
Consolidation Manifest
======================

Conventions (Derived)
---------------------
Naming: {tool}-reference.md for human-facing tool refs
        docs/tools/{tool}.md for per-tool setup guides
Inconsistencies: docs/tool-shortcuts.md → docs/tool-reference.md

KEEP (permanent reference):
  docs/architecture.md — system design, accurate
  docs/tools/lazygit.md — tool reference, current
  docs/fresh-install.md — onboarding, current

RENAME (naming inconsistencies vs. derived conventions):
  docs/tool-shortcuts.md → docs/tool-reference.md

ARCHIVE → docs/_archive/:
  docs/migration-plan-2024.md — migration complete (confirmed: all referenced paths exist)
  docs/old-runbook.md — describes decommissioned system

MOVE:
  config/editor/AGENTS.md (keybindings section) → docs/editor-reference.md
    Reason: human-facing content (actor test)

CREATE:
  docs/AGENTS.md — routing index for docs/ (currently missing)
  docs/tmux-reference.md — keybindings found in config/tmux/AGENTS.md, human-facing

NORMALIZE FRONTMATTER:
  docs/fresh-install.md — target docs tree establishes YAML indexing
    frontmatter; add missing id/title/description
```

**In PLAN mode**: Present this manifest and ask which actions to proceed with before touching any files.

**In AUTO mode**: Execute all actions after showing the manifest.

---

## Step 4: Execute

Execute in this order:

1. **Create** new files (gaps)
2. **Rename** files with naming inconsistencies (`git mv old new`)
3. **Move** content to correct locations (extract sections, don't duplicate)
4. **Archive** — move files to `docs/_archive/`, do not delete outright
5. **Update indexes** -- create or update `docs/README.md` (human progression) and `docs/AGENTS.md` (agent routing by doc type) to reflect all changes
6. **Normalize** frontmatter on files you touched only when their independently
   governed docs tree establishes that convention
7. **Verify** -- run the verification script (see SKILL.md Verification section
   for invocation) to check internal links, convention-conditional frontmatter,
   and index completeness. Fix any failures before reporting.

**Extracting sections from AGENTS.md** (Move step):
1. Read the full AGENTS.md
2. Identify the human-facing section(s)
3. Write extracted content to `docs/{topic}-reference.md`
4. Replace the extracted section in AGENTS.md with a cross-reference pointer:
   ```
   See the repository editor reference for keybindings.
   ```
5. Do not leave AGENTS.md shorter than it needs to be — preserve all agent-facing content

**Creating `docs/AGENTS.md`**:
- Lists every file in `docs/` with a one-line description
- Organized by category (reference, architecture, tools, runbooks)
- Agents load this to route into docs/ without reading every file

```markdown
# docs/ Index

| File | Purpose |
|------|---------|
| `architecture.md` | System design and component overview |
| `fresh-install.md` | Complete fresh-machine setup guide |
| `tools/lazygit.md` | lazygit keyboard reference |
```

---

## Step 5: Report

```
Consolidation Complete
======================
Kept: X files (no changes)
Renamed: R files (naming inconsistencies)
Archived: Y files → docs/_archive/
Moved: Z content sections
Created: N new files

Conventions derived:
  {tool}-reference.md for human-facing tool refs
  docs/tools/{tool}.md for per-tool setup guides

Renamed:
  docs/tool-shortcuts.md → docs/tool-reference.md ✅

New files:
  docs/AGENTS.md ✅
  docs/tmux-reference.md ✅

Archived:
  docs/migration-plan-2024.md → docs/_archive/migration-plan-2024.md ✅

Frontmatter normalized: M files

Remaining follow-ups:
  [any files kept as-is that need human review]
```

---

## Guardrails

- **Migrate means move** — when migrating content from a source (e.g., `agent_docs/`) to `docs/`, move the files (don't copy). No duplicated truth. If the source directory is empty after migration, remove it.
- **Archive superseded content** — if content is truly superseded (not migrated), move to `docs/_archive/` with a note. Don't delete outright.
- **Verify before archiving** — confirm the work/system described is actually gone before archiving its doc.
- **Don't reorganize AGENTS.md structure** — only extract human-facing content. Leave agent-facing content and structure intact.
- **One pass only** — don't recursively consolidate archived files.
- **Derive, don't impose** — conventions come from what already exists in the repo, not from an external template. If no clear pattern exists, don't invent one.
- **Update the index** — after any RENAME or MOVE, update `docs/AGENTS.md` to reflect the new paths.
- **P11 applies to all files** — sizing limits apply to pre-existing files too, not just newly generated ones. Flag files over 500L for splitting in the manifest. Files over 300L get a warning.
