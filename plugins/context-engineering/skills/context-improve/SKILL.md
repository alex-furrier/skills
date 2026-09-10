---
name: context-improve
description: >
  Improve AGENTS.md for a repo or module by detecting depth, optionally
  consuming user-provided session evidence, and delegating generation to
  context-agents-md. The canonical output shape is owned by context-agents-md.
  No docs/ by default.
---

## Portable deterministic evidence

The Context CLI and `uv` are required plugin dependencies. Install the complete Context plugin, including `cli/`; do not copy a Context skill alone. Run `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering ...`. If `uv`, the package, or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Context Improve

Use this skill to coordinate an AGENTS.md improvement for one repository or
module. It computes depth, accepts optional supplied session evidence, and hands
the proposal and any apply to `context-agents-md`.

## Activation and modes

Use **targeted** mode as `context-improve <repo-path>` when the target is known.
Use **general** mode as `context-improve` to choose a target; it does not scan
local agent history or claim automatic session mining.

## Inputs

Parse from `$ARGUMENTS`:
- `<repo-path>` — triggers **targeted mode**. Absolute or relative path.
- _(empty)_ — triggers **general mode**.
- `--docs` — opt-in: also run context-docs quickstart + consolidate (the old Phase A/B). Not default.
- `--skip-session-evidence` — skip optional session-evidence handling (Step 2).
- `--session <file.jsonl>` — targeted mode only. A user-supplied exported session artifact.
- `--sessions-dir <directory>` — user-supplied exported-session directory for a separately installed multi-session provider.
- `--help` — print usage and exit.

---

## General mode

Ask the user to select a target path, then use targeted mode. Session evidence
is unavailable by default. A separately installed multi-session provider may
supply ranked exported-session evidence only with user-supplied
`--sessions-dir`; this skill does not provide, install, or emulate that provider.

---

## Targeted mode

### Step 1: Validate Inputs + Depth Detection

**Resolve scope and git root.** Find the git root with
`git -C <repo-path> rev-parse --show-toplevel`. Compute depth:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering depth <target-path> --json
```

The subcommand accepts either an AGENTS.md file (runs full stringency checks) or a
directory (computes depth only — use this in quick-start mode when AGENTS.md
doesn't exist yet). If the command fails or is unavailable, stop; do not count
path segments inline.

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

### Step 2: Optional Session Evidence

**Skip when `--skip-session-evidence` is set.** Session evidence is unavailable
unless the user supplies an exported-session directory and an actually installed
separate multi-session provider. Do not scan local history, use a sibling skill,
or substitute the shared CLI for that provider; none is shipped by this skill.

A user may instead provide `--session <file.jsonl>` as a single exported
artifact. Otherwise, state `session_evidence: unavailable` and continue with
existing context and code analysis. Pass only user-supplied or separately
provider-produced candidates, with source attribution, to the owner.

---

### Step 3: Delegate AGENTS.md Review and Apply

Load the `context-agents-md` skill (sibling skill). Pass it:
- The target path
- Depth level
- Any attributed session-evidence candidates from Step 2

Context-agents-md owns the generated AGENTS.md output shape, section order,
interactive review, authorized apply, post-write validation, and
`CLAUDE.md → AGENTS.md` handling. It also owns skipped-candidate triage and the
proposal/apply boundary for `SKIPPED_FOR_REVIEW.md`. Do not redefine, prune, or
repeat that contract here, and never create or modify any of those files here.
Consume its interactive-review result and, after authorized apply, its
post-write validation result in the report.

---

### Step 3b: Context Docs (opt-in)

**Only runs if `--docs` flag is set.**

Load the `context-docs` skill and run quickstart + consolidate on the target.
This creates the `docs/` directory structure with intent-based folders.

Note: this is the old Phase A/B flow, now opt-in. Most modules don't need it —
lean AGENTS.md is the default.

---

### Step 4: Report

Print a summary:

```markdown
# Context Improve — <target> — YYYY-MM-DD

## Delegated AGENTS.md Result
- Owner: `context-agents-md`
- Review: <presented/accepted/revisions requested>
- Apply authorization: <authorized/not authorized>
- AGENTS.md: <created/updated only after authorized apply, or unchanged>
- CLAUDE.md symlink: <created/exists/unchanged>

## Owner Validation
- References: <owner result>
- Depth stringency: <owner result>
- Antipatterns: <owner result>
- Frontmatter: <owner post-write result when --docs applies, or not run>

## Session Evidence
- Availability: <available/unavailable/skipped>
- Source: <user-supplied export/installed provider/not available>
- Gotcha candidates found: <N or not available>
- Owner skipped-candidate disposition: <included/relocated/reviewed/dropped/not applicable>

## Next Steps
- Authorize the owner apply only after reviewing its proposed AGENTS.md change.
- To add docs/ structure: re-run with `--docs`
```

---

## Quality Rules

- **Depth detection is mandatory** — always compute and surface before generation.
- **Session evidence is optional** — use only attributed user-supplied exports or output from a separately installed provider. Otherwise report it as unavailable and continue.
- **Canonical output is delegated** — `context-agents-md` owns AGENTS.md
  sections and content rules; this skill does not redefine them. Docs remain
  opt-in.
- **Owner review before write** — `context-agents-md` presents interactive
  review before any write, applies only with explicit authorization, then runs
  and reports post-write validation.
- **One module per run** — don't attempt multiple modules in one invocation.
- **Worktree preferred** — suggest worktree isolation; don't pollute main.

## Known Limitations

This skill is a workflow orchestrator — it loads sibling skill SKILL.md bodies
inline and executes their steps directly (skills can't recursively load other
skills as subagents in Claude Code).

If a sibling skill is not available (SKILL.md not found), the step is skipped
with a warning and the user is told to run it manually.
