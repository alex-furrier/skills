---
name: context-improve
description: >
  Generate lean, session-mined AGENTS.md for a repo or module. Two modes:
  targeted (given a path, detect depth, mine sessions, generate orientation +
  gotchas) and general (no args — scan recent sessions, rank repos by signal
  density, let user pick). Default output is portable lean shape: 1-2 sentence
  orientation + DO/NOT/BECAUSE gotchas. No docs/ by default.
---

## Portable deterministic evidence

The Context CLI and `uv` are required catalog dependencies. Install the complete catalog, including `packages/context-engineering`; do not copy a Context skill alone. Run `uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering ...`. If `uv`, the package, or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Context Improve

Two modes with different entry points:

**Targeted** (`context-improve <repo-path>`) — you know which module needs work.
Detects depth, mines sessions, generates lean AGENTS.md.

**General** (`context-improve`) — discovery first. Scans recent sessions, groups
by detected repo, ranks by signal density, presents candidates. You pick, then
it runs targeted mode.

## Inputs

Parse from `$ARGUMENTS`:
- `<repo-path>` — triggers **targeted mode**. Absolute or relative path.
- _(empty)_ — triggers **general mode**.
- `--auto` — skip interactive review. Include only clean-validated items. Emit `SKIPPED_FOR_REVIEW.md` for items needing human decision.
- `--docs` — opt-in: also run context-docs quickstart + consolidate (the old Phase A/B). Not default.
- `--skip-session-evidence` — skip optional session-evidence discovery (Step 2).
- `--session <file.jsonl>` — targeted mode only. Specific session to mine.
- `--max-sessions <n>` — max sessions to scan. Default: 20.
- `--help` — print usage and exit.

---

## General Mode (no repo-path provided)

Discover which modules in the current repo have session history worth mining.

Use the shared CLI's `sessions` subcommand with the current directory to
find sessions that mention this repo:

```bash
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering sessions "$(pwd)" --max ${MAX_SESSIONS:-20} --json
```

This returns sessions ranked by relevance to the current directory. Skim the top
sessions for correction/pivot signals, then suggest a target path to the user:

```
Found 5 sessions mentioning this repo. Top signals:
  - services/payments/: 3 sessions, heavy correction activity
  - packages/recommendations/models/ranker/: 2 sessions

Which module should I run context-improve on? (path, or 'q' to quit)
```

Wait for user selection. Then run targeted mode on the selected path.

---

## Targeted Mode

### Step 1: Validate Inputs + Depth Detection

**Resolve scope and git root.** Find the git root with
`git -C <repo-path> rev-parse --show-toplevel`. Compute depth:

```bash
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering depth <target-path> --json
```

The subcommand accepts either an AGENTS.md file (runs full stringency checks) or a
directory (computes depth only — use this in quick-start mode when AGENTS.md
doesn't exist yet). Fallback: count path segments from git root to target inline.

**Surface depth to user before any generation:**
- depth 0 → "Target: repo root. Stringency: maximum. Only cross-cutting invariants."
- depth 1 → "Target: top-level module. Stringency: strict. Module-wide content only."
- depth 2+ → "Target: leaf module. Stringency: normal."

**Detect project domain** by skimming README and top-level structure:
- Language/framework
- Existing context files: any `AGENTS.md`, `CLAUDE.md`, `docs/` already present?

Log:
```
Target: <path>
Git root: <root>
Depth: <N> — Stringency: <level>
Existing context: <what was found>
```

**Recommend worktree** for isolation if not already in one.

---

### Step 2: Session Mining

**Skip when `--skip-session-evidence` is set.**

Discover sessions relevant to the target path:

```bash
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering sessions <target-path> --max ${MAX_SESSIONS:-20} --json
```

Load the a separate multi-session workflow skill (sibling skill in this plugin). Pass it:
- The target path
- The discovered sessions (or `--session` if specified)
- A manifest with depth and existing AGENTS.md state

Session-reflect will:
1. Read existing AGENTS.md (if any) to check capacity and existing content
2. Aggregate relevant sessions
3. Extract behavioral patterns (corrections, re-explanations, pivots)
4. Return candidate gotchas with source attribution

Capture the candidate list for Step 4.

---

### Step 3: Generate AGENTS.md

Load the `context-agents-md` skill (sibling skill). Pass it:
- The target path
- Depth level
- Session-mined candidates from Step 2

Context-agents-md generates the lean output:
- 1-2 sentence orientation (entry point + key config)
- Gotchas section (DO/NOT/BECAUSE bullets)
- Symlink: `CLAUDE.md → AGENTS.md`

After running: confirm AGENTS.md created/updated.

---

### Step 3b: Context Docs (opt-in)

**Only runs if `--docs` flag is set.**

Load the `context-docs` skill and run quickstart + consolidate on the target.
This creates the `docs/` directory structure with intent-based folders.

Note: this is the old Phase A/B flow, now opt-in. Most modules don't need it —
lean AGENTS.md is the default.

---

### Step 4: Validate

Run validation scripts against the target:

```bash
# Frontmatter checks (only relevant if --docs was used)
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering frontmatter <target>

# Path reference checks
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering references <target>

# Antipattern + depth-tiered line limits
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering antipatterns <target>

# Depth stringency
uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering depth <target>/AGENTS.md
```

Fix blocking failures (broken refs). Review non-blocking warnings.

---

### Step 5: Interactive Review

**Skip if `--auto` is set.**

Present generated content section-by-section with validation status:

```
=== AGENTS.md for <target> (depth <N>) ===

Orientation:
  <the 1-2 sentence orientation paragraph>

Gotcha candidates:
 1. DO <action>. NOT <mistake>. BECAUSE <reason>.
    [validated | source: session-history 3/5 sessions]

 2. DO <action>. NOT <mistake>. BECAUSE <reason>.
    [plausible, not validated | source: code comment]

 3. DO <action>. NOT <mistake>. BECAUSE <reason>.
    [validated | source: session-history + code analysis]

Keep which? [numbers, "all", "none", or "2 should be reworded"]
Default: all validated. Reply "ok" to accept.
```

Process user response:
- Numbers (e.g., "1 3") → keep only those
- "all" → keep everything
- "none" → keep only orientation
- Reword request (e.g., "2 should say X instead") → apply and re-show
- "ok" → accept the default (all validated items)

**Auto mode**: skip this step entirely. Include only clean-validated items.
Write unvalidated candidates to `SKIPPED_FOR_REVIEW.md` in the target directory
with a note: "Review these candidates and add to AGENTS.md if accurate."

---

### Step 6: Report

Print a summary:

```markdown
# Context Improve — <target> — YYYY-MM-DD

## Output
- AGENTS.md: <created/updated> (<N> lines, depth <D>)
- CLAUDE.md symlink: <created/exists>

## Validation
- References: <pass/N failures>
- Depth stringency: <pass/N warnings>
- Antipatterns: <N warnings>

## Session Mining
- Sessions scanned: <N>
- Gotcha candidates found: <N>
- Included: <N> | Skipped for review: <N>

## Next Steps
- Review AGENTS.md in context: `cat <target>/AGENTS.md`
- To add docs/ structure: re-run with `--docs`
```

---

## Quality Rules

- **Depth detection is mandatory** — always compute and surface before generation.
- **Session mining is default** — skip only when explicitly asked.
- **Lean output by default** — orientation + gotchas. No architecture prose, no commands table, no docs/.
- **Interactive by default** — let the user review and prune before finalizing.
- **One module per run** — don't attempt multiple modules in one invocation.
- **Worktree preferred** — suggest worktree isolation; don't pollute main.

## Known Limitations

This skill is a workflow orchestrator — it loads sibling skill SKILL.md bodies
inline and executes their steps directly (skills can't recursively load other
skills as subagents in Claude Code).

If a sibling skill is not available (SKILL.md not found), the step is skipped
with a warning and the user is told to run it manually.
