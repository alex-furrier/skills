# Generated AGENTS.md Specification

Exact structure and content guidelines for generated AGENTS.md files. All generated
files follow this template.

## Contents
- Required structure (watermark, capture authority, WHY/HOW, commands, invariants, gotchas, pointers)
- CLAUDE.md strategy (symlink + consolidation workflow)
- Nested AGENTS.md guidelines
- Command validation rules
- Things to absolutely avoid

## Required Structure

### 1. Generation watermark

AGENTS.md files are routing indexes and do **not** get YAML frontmatter.
Instead, add an HTML comment watermark at the end of the file:

```markdown
<!-- generated-by: context-engineering@1.0.0 | last-updated: 2026-04-02 -->
```

This watermark is invisible to readers but greppable for tracking adoption and staleness.

### 2. Capture authority

Start generated context with the project orientation. Do not add compulsory
mid-task correction capture. Preserve useful corrections as evidence for an
explicitly authorized context update, not as automatic write authority. The
owning `context-agents-md` skill routes later capture to `session-capture` when
available and otherwise proposes the update without writing it.

### 3. Project Overview (WHY)

1-3 paragraphs: what it is, who uses it, what "done" means.

### 4. How to Work Here (HOW)

Short workflow guidance (explore → plan → implement → validate).
Explicit validation expectations (what must pass before committing).

### 5. Common Commands (validated)

Compact list with validation markers:
- ✅ executed successfully
- ⚠️ executed but failed (include reason + fix suggestion)
- ⏸️ not executed (include why and how to run)

**Critical rule — no fast-changing specifics:**
Never include specific counts, timing, or other numbers that go stale.

| Write this | Not this |
|-----------|---------|
| `uv run pytest tests/unit/ -v` — run the unit test suite | `uv run pytest tests/unit/ -v` — runs 159 tests in 8.2s |
| `mise run test` — run all tests (includes E2E, slower) | `mise run test` — runs 342 tests across 24 modules |
| `mise run check` — fast quality gate | `mise run check` — completes in ~15s |

Counts go stale the moment someone adds a test. The command doesn't.

### 6. System Invariants

Rules that if violated break everything downstream. Separate from gotchas.

> These rules prevent catastrophic mistakes. Violating them may require
> reverting or significant cleanup.

**Format:**
```
- **{Invariant name}**: {What must always be true}. Violation causes: {consequence}.
```

**Examples:**
- **Forward-only migrations**: Database migrations never include rollback scripts. Violation causes: schema inconsistency across environments.
- **Auth on all endpoints**: Every public API endpoint declares an auth model before merge. Violation causes: unauthenticated access to protected resources.
- **CI parity**: `mise run check` locally must match what CI runs. Violation causes: green local / red CI divergence.

**Guidelines:**
- Keep invariants concise in AGENTS.md. When AGENTS.md approaches 250 lines, move detailed invariants to `docs/invariants.md` and keep 1-line summaries here.
- Only include invariants discoverable from code, CI, or config — do not speculate.
- Mark unverified invariants with `REVIEW:` prefix for human review.
- Higher stakes than gotchas. Wrong invariants are worse than no invariants.

### 7. Gotchas

Every gotcha follows the **DO / NOT / BECAUSE** pattern:

**Format:**
```
- **DO** {correct action}. **NOT** {common mistake}. **BECAUSE** {rationale}.
```

**Examples:**
- **DO** run `uv run pytest tests/unit/ -v` for fast validation. **NOT** `mise run test` (runs full suite including integration). **BECAUSE** integration tests require network access and are significantly slower; unit tests provide fast feedback.
- **DO** edit brewfiles in `brewfiles/` directory. **NOT** `provisioning/pyinfra/vars/packages.yml` for Homebrew packages. **BECAUSE** packages.yml is for apt/dnf system packages; Homebrew has its own brewfile system.
- **DO** use `uv run` for Python commands. **NOT** bare `pip` or `python`. **BECAUSE** uv manages the virtualenv and ensures reproducible dependency resolution.

**Guidelines:**
- Only high-impact, stable surprises not obvious from code
- The redirect (what TO do) is mandatory — an alternative is worth more than a warning
- Never include specific timing or counts (apply the no-fast-changing-specifics rule)

### 8. Progressive Disclosure Pointers

Lightweight pointers — don't enumerate every file, just tell the agent where to look:

```markdown
## Task-Specific Docs

### Nested module docs (auto-discovered by Claude Code)

| Path | Topic |
|------|-------|
| `module/AGENTS.md` | Brief description |

### Cross-cutting docs

See `docs/` for detailed documentation (architecture, testing, interfaces, etc.).
Run `ls docs/` or `tree docs/` to discover what's available.
```

Keep this section short. The `docs/` directory has its own `AGENTS.md` index that provides full routing — this section is just a pointer to get the agent there.

### 9. Key References

Links to authoritative docs, config files, external resources.

---

## Docs ownership boundary

This skill may link an existing `docs/` tree from AGENTS.md, but it does not
create or reorganize docs content or docs indexes. Route that work to
`context-docs`, which owns `docs/README.md`, `docs/AGENTS.md`, explanation, and
reference material. Repeatable procedures remain skills.

---

## CLAUDE.md Strategy

Default: CLAUDE.md is a symlink to AGENTS.md.

### Consolidation Workflow

**Detection**: Check if CLAUDE.md is a symlink (`ls -la CLAUDE.md`).

**Interactive modes (quick-start, update, evaluate)**: Ask the user:
> "CLAUDE.md exists as a standalone file. Consolidate into AGENTS.md and replace
> with a symlink?"

**Auto mode**: Consolidate automatically:
1. Read both files
2. Merge: deduplicate, prefer more accurate content, reconcile contradictions
3. Write merged content to AGENTS.md
4. Remove standalone CLAUDE.md
5. Create symlink: `ln -s AGENTS.md CLAUDE.md`
6. Report what was merged

**Merge strategy:**
- Only CLAUDE.md exists → rename to AGENTS.md, create symlink
- Both exist → merge by WHY/HOW sections, keep most complete version of each
- Preserve unique CLAUDE.md content that doesn't exist in AGENTS.md

---

## Nested AGENTS.md Guidelines

Same WHY/HOW structure, scoped to the module.
Always create CLAUDE.md symlink alongside.
Same validation markers. No frontmatter (AGENTS.md files are routing indexes).

---

<!-- environment-specific-dependencies:v1 -->
## Environment-Specific Dependencies

Label local wrappers, private CLIs, absolute home paths, credential profiles,
and user-specific automation as environment-specific. State the dependency,
installation source, vanilla/portable fallback (or that none exists), and
missing-tool behavior. Never emit a personal command as a universal
prerequisite.

## Command Validation Rules

For each command listed:
1. Confirm it exists (package.json scripts, Makefile target, CI step)
2. If feasible, run a non-destructive validation (`--help`, list scripts/targets, dry-run)
3. Record status as ✅ / ⚠️ / ⏸️

**Test command rules (required when feasible):**
- Attempt a minimal, safe, fast test execution to prove the harness works
- Avoid anything long-running, networked, E2E, integration, or data-mutating
- Do NOT run targets containing: `e2e`, `integration`, `playwright`, `cypress`,
  `selenium`, `docker`, `compose`, `migrate`, `seed`, `reset`, `drop`
- Prefer "unit/smoke/short" targets or "collect only/dry-run" mode
- If cannot confidently keep it fast/offline, mark ⏸️ and explain

---

## Audience Filter: Agent vs Human Content

Before routing any content, apply the **actor test**: *who does this?*

**Agent-facing → AGENTS.md** (nested, load-on-demand):
- **Script purpose tables** (when/why to run each script) — agent calls these
- **Build/test/lint commands** — agent invokes these
- **Invariants, gotchas** — agent must not violate these
- **Progressive disclosure pointers** to docs/ and nested AGENTS.md — agent follows these

**Human-facing → `docs/{topic}-reference.md` or `README.md` alongside the config**:
- **Interactive keyboard shortcuts** (editor, terminal, IDE keybindings) — humans press keys; agents don't
- **Shell aliases and shorthand commands** typed at a prompt — humans type them; agents invoke full commands
- **UI or display preferences** (color themes, pager settings, prompt style) — humans configure these
- **Daily-use cheat sheets** and personal workflow references — for humans operating the tool

The test is not about content type or durability. Stable, accurate content is still human-facing if a human is the actor. Route it to `docs/` where both humans and agents can find it on demand, but keep AGENTS.md focused on what agents actually need to do their job.

## Procedural routing

Do not generate docs as an intermediate step for reusable procedures. When an
AGENTS.md audit identifies a repeatable agent-executable workflow, propose a
skill directly and include the source context plus activation trigger. Route
docs analysis or reorganization to `context-docs`.

**Repo layout for skills**: Author skills in `.agents/skills/` (tool-agnostic),
symlink from tool-specific config dirs. This mirrors the AGENTS.md/CLAUDE.md
symlink convention — one source of truth, multiple consumers.

```
repo/
  .agents/
    skills/
      test-failure-triage/
        SKILL.md           ← canonical location
  .claude/
    skills -> ../.agents/skills   ← Claude Code reads here
```

Codex reads `.agents/skills/` natively — no symlink needed. Claude Code needs
the `.claude/skills` symlink. As more tools adopt `.agents/`, the symlinks
become unnecessary.

**Module-scoped skills** (monorepo): each module gets its own `.agents/skills/`
with its own `.claude/skills` symlink. This preserves scoped discovery — agents
only see a module's skills when working in that subdirectory.

```
packages/
  payments/
    .agents/skills/payment-reconciliation/SKILL.md
    .claude/skills -> ../.agents/skills
  web/
    .agents/skills/frontend-a11y/SKILL.md
    .claude/skills -> ../.agents/skills
```

**Do not auto-create skills.** Only suggest — the user decides what to promote.
Skill promotion is a separate step that deserves its own review.

---

## Things to Absolutely Avoid

- Long style guides (prefer "run formatter/linter X")
- Huge auto-generated command outputs, tool listings with output (not reference tables)
- Copy-pasted code that will go stale (prefer `file:line` references)
- Fast-changing specifics (test counts, timing data, line counts, module counts)
- Speculative invariants (only document what's discoverable from code/CI)
- Human-facing content in AGENTS.md (interactive shortcuts, shell aliases, display preferences) — route to `docs/` instead
