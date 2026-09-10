---
name: context-agents-md
description: "Generate lean AGENTS.md files with a short orientation and DO/NOT/BECAUSE gotchas. Uses depth-aware stringency, validated commands, and session-mined content. Use when creating or updating agent context files for any repo or module."
---

**Watermark**: All generated AGENTS.md files include a `generated-by` watermark.
Portable catalog release: `safurrier-skills`; its Context CLI, `uv`, and plugin-local `cli/` project are required dependencies.

## Output Shape (North Star)

The following portable shape is
the target for every generated AGENTS.md:

```markdown
## Portable deterministic evidence

The Context CLI and `uv` are required plugin dependencies. Install the complete Context plugin, including `cli/`; do not copy a Context skill alone. Run `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering ...`. If `uv`, the package, or the command is unavailable, stop the requested deterministic-analysis workflow and report the missing dependency; do not substitute read-only inspection or claim equivalent evidence.

# Module Name

One-to-two sentence orientation. Entry point: `ClassOrFunc` in `path/file.py`.
Key config: `OTHER_THING` (`other/file.py`).

## Gotchas

- **DO** <specific action>. **NOT** <specific mistake>. **BECAUSE** <rationale>.

- **DO** ... **NOT** ... **BECAUSE** ...

## Related Context                          ← include when cross-cutting deps exist

| Path | What's there |
|------|-------------|
| `../sibling/AGENTS.md` | Sibling module context |
| `shared_constants/` | Constants shared across modules |
```

**Auto mode** (`--auto`) and **interactive mode** (default) emit the same
section set — the distinction is whether the user reviews candidates before
they land. Both modes follow the canonical section order from Step 4 and
apply the tier rules from Step 3c. Interactive mode adds a human-review step
between generation and write; auto mode writes directly using clean-validated
content, with skipped candidates landing in `SKIPPED_FOR_REVIEW.md`.

**Never add in any mode:**
- Architecture prose — CRUD layering descriptions, dependency graphs
- Directory layouts, key paths tables, file maps
- Deployment instructions (human-facing, P5)

Commands live in the dedicated `## Commands` section (single-path always
included; multi-path gated by tier). They only also appear inside a gotcha
bullet when the gotcha is specifically about a non-obvious use of that command.

## Core Rules

* **Default shape**: orientation + optional How-to-Work-Here (tier-gated) + Commands + Gotchas + Related Context. Both auto and interactive mode emit the same sections; interactive adds a human review step before write.
* **Correction capture**: do not insert a compulsory mid-task capture paragraph. A correction is evidence to consider, not authority to write durable context or interrupt the current assignment. Use `session-capture` for later user-approved capture; if unavailable, propose the narrow update without writing it. Explicitly authorized context maintenance remains in scope.
* **Gotchas include code traps**: a gotcha doesn't require session history. If an agent would almost-get-it-right but subtly wrong based on code patterns (e.g., patching at the wrong module path, using the wrong base class), that's a valid DO/NOT/BECAUSE bullet.
* **Related Context section**: include when cross-cutting dependencies exist (sibling modules, shared constants, config dirs). These pointers save agents from missing non-obvious connections. Keep it to a compact table.
* **Commands section**: single-path commands always included; multi-path commands scaled by contributor tier (see Step 3c). Commands are reference lookup, not workflow opinion.
* **How to Work Here**: tier-gated workflow prescription. Drop at 21+; opinionated candidates go to `SKIPPED_FOR_REVIEW.md`.
* **No architecture prose**: CRUD layering descriptions, dependency graphs, directory layouts, and file maps are discoverable by reading code. Don't include them.
* **Every token earns its place** (P2): for each line, apply the removal test: "Would removing this cause Claude to make mistakes?" If no, cut it.
* **Depth-aware stringency** (P3): the higher up the repo, the stricter the bar. See depth table below.
* **Audience filter** (P5): agent does it → AGENTS.md; human does it → docs/.
* **DO/NOT/BECAUSE** (P7): every gotcha follows this format. DO comes first.
* **Validate what you claim** (P13): confirmed → include. Can't validate → drop. Plausible but unvalidated → surface in interactive flow; drop in `--auto`.
* **No emoji markers in final output**: ✅/⚠️/⏸️ appear only in the internal candidates list during interactive review.
* **Session-history attribution**: preserve HTML comment `<!-- source: session-history | session: <id> | extracted: YYYY-MM-DD -->` for session-derived content.

Security/ops guardrails:
* Never write secrets into generated files.
* Do not run destructive shell commands.
* Prefer offline validation; avoid networked commands unless explicitly asked.
* Label local wrappers, private CLIs, absolute home paths, credential profiles,
  and user-specific automation as environment-specific. Name the dependency and
  installation source, give a vanilla/portable fallback (or state that none
  exists), and define missing-tool behavior. Put
  `<!-- environment-specific-dependencies:v1 -->` immediately before governed
  dependency headings so future audits and migrations can find them. Never
  present a personal command as a universal prerequisite.

Full principles: `README.md`

## Depth Stringency

Compute depth from git root. Apply the appropriate bar:

| Depth | Location | Gotcha bar | Commands bar |
|---|---|---|---|
| 0 | Repo root | Cross-cutting invariants only | Near-zero — defer to module AGENTS.md |
| 1 | Top-level module | Module-wide only | Strict — validated AND applies to whole module |
| 2+ | Leaf module | Normal — non-obvious gotchas | Normal — validated + non-obvious |

At depth 0: any content that's module-specific should be flagged as "needs deeper scope."
At depth 1: validate that every gotcha applies to the entire module, not just a subfolder.

## Inputs

RAW ARGUMENTS: `$ARGUMENTS`

If `$ARGUMENTS` contains `--help` or is exactly `help`, print usage and exit.

### Parsing

1. Extract flags: `--help`, `--agents`, `--claude`, `--both` (default: `--both`), `--auto`
2. Parse remaining as: `[mode] [scope...]`
3. Defaults: mode=`auto`, scope=`.`

## Modes

**quick-start**: Create from scratch. Output is orientation + gotchas.

**update**: Incremental. Run `uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering staleness <path-to-AGENTS.md> --json` to assess what changed. Inspect every reported path and classification reason before choosing scope; the recommendation is advisory.
Only update affected sections. Use a full scan only after independently verifying one
of the force conditions in `references/incremental-update-workflow.md`.

**evaluate**: Everything in update, plus evaluate against principles and propose improvements.

**auto** (default): No AGENTS.md → quick-start. Has AGENTS.md → update + evaluate.
Zero user input. Only includes clean-validated content.

---

## Execution

### 1. Determine Root, Scope, and Depth

* Find git root: `git -C <scope> rev-parse --show-toplevel`
* Compute depth (segments from git root to target)
* Detect monorepo signals (workspaces, multiple manifests)
* In auto mode: infer scope from `git status` if not provided

### 2. Discover Authoritative Context

Read (minimal, targeted):
- README, build/test configs, package manifests
- Existing AGENTS.md / CLAUDE.md (read before overwriting)

### 3. Collect Gotcha Candidates

Sources (in priority order):
1. **Optional multi-session evidence** — use a user-supplied session summary or a separately installed evidence provider when available. If neither is available, state `session_evidence: unavailable` and continue with existing context and code analysis.
2. **Existing AGENTS.md content** — preserve accurate gotchas, prune stale ones.
3. **Code analysis** — non-obvious patterns discoverable only by reading code: race conditions, import-time side effects, test harness quirks, config gotchas.

For each candidate, classify:
- **Validated**: command runs, path exists, behavior confirmed → include.
- **Can't validate**: command missing, path wrong → drop entirely.
- **Plausible**: looks right but can't confirm without E2E → surface in interactive flow; drop in `--auto`.

Before including a command, classify its portability. If it is a local wrapper,
private CLI, absolute home path, credential profile, or user-specific
automation, keep it only with an environment-specific label, dependency,
installation source, portable fallback (or explicit no-fallback statement), and
missing-tool behavior. Add `<!-- environment-specific-dependencies:v1 -->`
immediately before the governed dependency heading.

### 3b. Gather Related Context candidates

The goal: identify a handful of other modules a fresh agent would benefit from
knowing about. Use multiple sources — the script is one signal, not the only one.

**Sources** (combine, don't rely on any single one):

1. **Code exploration** — read the target's imports, config paths, data
   contracts, and references to external services. Follow what the code
   actually touches.
2. **Existing docs** — if the target already has a README or AGENTS.md, any
   "see also" / "related" sections are a valuable starting point.
3. **Session history** — if a separate multi-session workflow ran in Step 2, patterns
   about cross-module issues are signal.
4. **`map_cross_cutting.py --discover`** — runs import / git co-change /
   author-overlap analysis. High recall, surfaces non-obvious coupling
   (shared protos, orchestration systems, sibling services) that code
   reading alone misses:

   ```bash
   uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering cross-cutting <target> --discover --lookback-days 180 --top 12 --json
   ```

Combine all four sources, then filter to 3-6 entries using the decision rule:
**"would a fresh agent working on this module benefit from knowing about this
other module's existence?"** If no clear answer, cut it.

Rough filtering guidance:
- **Keep**: shared contracts (protos, config keys), sibling modules that
  evolve together, upstream services the target consumes, orchestration
  systems that call the target, any module an existing gotcha references.
- **Cut**: parent directories (trivial), generic infra buckets that everyone
  touches (e.g., `shared`, `documentation`, `misc`) unless the coupling
  is specifically meaningful, buckets without an articulable shared contract.
- **Author-overlap signals** are useful for understanding team ownership but
  usually don't belong in the Related Context table — drop them by default.

If the script returns little signal (e.g., fresh module with no history), that's
fine — rely on code exploration instead. Related Context can be empty if
nothing meaningful is coupled.

### 3c. Contributor-signal check (prescriptivity prior)

Classify the module's tier via the shared CLI:

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering tier <target> --json
```

Returns `tier` ∈ `{1, 2-5, 6-20, 21+}` plus plain-language guidance for
multi-path commands, How to Work Here, and gotcha budget. Use as a **prior**
for how opinionated to be — not a rule. The AI deviates with reason.

**Command classification — the key v2.1 distinction:** before including a
command, ask "is there ONE right way, or multiple valid paths?"

- **Single-path** (`clint lint --fix`, `clyde migrate apply`, canonical build/run
  entry): include plainly regardless of tier.
- **Multi-path** — genuinely distinct tools or entry points with different
  tradeoffs (e.g. `./api-test-with-daemon.sh` vs `clyde api test` vs
  `clyde api test --magic`). Picking one IS opinion. Gate by tier:
  - **1 / 2-5**: pick a default with a one-line rationale
  - **6-20**: list options with tradeoff notes, no prescribed default
  - **21+**: list neutrally, or defer to `--help` / nested AGENTS.md

Rule of thumb: if the choice changes *how tests run* (env, speed, tool) it's
multi-path. If it changes *which tests run* (filter/marker) it's single-path.

**How to Work Here** (sequence/onboarding flow): include only where the tier
allows opinion. Drop entirely at 21+; candidates go to `SKIPPED_FOR_REVIEW.md`.

**Gotcha budget** (soft filter, not hard cap):
- < 10 gotchas → keep all validated
- 10-15 → apply P2 harder, drop lint-enforced style items
- > 15 → flag as splitting candidate, overflow hierarchy applies

### 4. Write AGENTS.md

**Canonical section order:**

```markdown
# <Module Name>

<1-2 sentence orientation. Entry point and key config.>

## How to Work Here           ← only if tier allows (1 / 2-5 / 6-20)
<brief onboarding flow — read X, then Y, then open a PR>

## Commands
**Lint/format**: <single-path command>.
**Testing**: <for multi-path at 21+, list options neutrally with tradeoffs>.
**<other>**: <single-path command with context if relevant>.

## Gotchas
- **DO** <action>. **NOT** <mistake>. **BECAUSE** <rationale>.
<!-- source: session-history | session: <id> | extracted: YYYY-MM-DD -->

- **DO** <action>. **NOT** <mistake>. **BECAUSE** <rationale>.

## Related Context            ← from Step 3b, 3-6 entries
| Path | What's there |
|------|-------------|
| `../sibling/AGENTS.md` | <why an agent benefits from knowing it exists> |
```

Append watermark as last line:
```markdown
<!-- generated-by: context-engineering@X.Y.Z | last-updated: YYYY-MM-DD -->
```

**CLAUDE.md**: symlink to AGENTS.md. Create if it doesn't exist:
```bash
ln -sf AGENTS.md CLAUDE.md
```

**Sequence vs command-knowledge rubric** (for placing context about *when* a
command is used):
- Value is in the **command context** (flags, when it's relevant): Commands
  entry with inline context. Example: `Migrations: clyde migrate apply — run
  after pulling or switching branches, before clyde start.`
- Value is in the **sequence/ordering** (A then B then C, pipeline matters):
  How to Work Here.
- Value is a **specific trap within a step** (the MFA ticket exchange is
  non-obvious): gotcha.

**Gotcha ordering**: most dangerous first (race conditions, data loss risks),
then workflow gotchas, then style/convention gotchas.

### 4c. Relocate before you drop

For every candidate that won't be included (existing AGENTS.md content that
violates tier/budget/depth, new candidates that didn't make the cut), triage
into three buckets — don't just delete:

1. **Relocate** — accurate + useful + has a clearly-better canonical home (a
   nested AGENTS.md, an existing skill, a module doc). Write to the
   `## Relocate` section of `SKIPPED_FOR_REVIEW.md` with the destination path.
2. **Review** — useful but no obvious home. Write to the `## Review` section.
3. **Drop** — no longer accurate, duplicates canonical, enforced by tooling.
   Write to the `## Drop` section with the reason.

**`SKIPPED_FOR_REVIEW.md` format:**

```markdown
# SKIPPED_FOR_REVIEW — <module> — <YYYY-MM-DD>

## Relocate — content with a clearly-better canonical home

### <topic>
- **Proposed destination**: `<path>/AGENTS.md` (create if missing)
- **Why relocate**: <principle or tier reason>
- **Content**: <the actual text or a quote>

## Review — candidates without an obvious home

### <topic>
- **Why skipped**: <reason>
- **Recommended action**: <human decision needed>

## Drop — no longer accurate or already canonical elsewhere

### <topic>
- **Why dropped**: <reason — enforced by lint, duplicates README, etc.>
```

If there's nothing to relocate/review/drop, don't create the file.

### 5. Validate

Run validation via the shared CLI (paths are relative to this skill's directory):

```bash
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering frontmatter <target>           # only if docs/ exist
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering references <target>            # path reference checks
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering antipatterns <target>          # volatile content, line limits, density, splitting-candidate
uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering depth <target>/AGENTS.md       # depth-appropriate content
```

The `antipatterns splitting-candidate` warning fires when 3+ gotcha
bullets reference paths under a common subdirectory — signal that the module
may want horizontal splitting (see Overflow hierarchy in principles.md).

Distinguish between new failures (in files you created — fix them) and
pre-existing failures (in unmodified files — report as-is).

### 6. Report

Output in chat:
* Files created/updated (paths)
* Line count, depth, **contributor tier** (from Step 3c)
* Commands classification: how many single-path vs multi-path
* Gotchas included vs. skipped (relocate / review / drop)
* Validation results
* **`splitting-candidate` warnings** — if any, recommend concrete next step
  (promote to `<subdir>/AGENTS.md`)
* **Skill candidates** (P12): procedural how-to content that should become
  skills. Propose; don't auto-create.
* Any follow-ups

Do NOT paste full file contents unless asked.

---

## Scripts

Deterministic validation tools in `scripts/`:

Invoke via the shared CLI (from this skill's directory):
`uv run --no-config --locked --no-dev --project <context-plugin-root>/cli context-engineering <subcommand>`

| Subcommand | When to run | What it does |
|------------|-------------|-------------|
| `frontmatter {path}` | After generating docs/ content | Checks frontmatter fields, unique ids |
| `staleness {agents-md}` | Start of update mode | Git-based staleness assessment |
| `references {path}` | After generating/updating docs | Confirms backtick paths exist |
| `antipatterns {path}` | After any generation | Volatile content, depth-tiered line limits, section density, splitting-candidate |
| `depth {path}` | After generating AGENTS.md | Depth-appropriate content check |
| `sessions {path}` | Session discovery | Find relevant sessions for a target path |
| `cross-cutting {path} --discover` | Step 3b — Related Context candidates | Surface modules coupled via imports, git co-change, and author overlap |
| `tier {path} --json` | Step 3c — prescriptivity tier | Classify module by unique-author count into tier with plain-language guidance |

---

## Bundled Content

Load only what the current step requires:

**Resources** (specs and templates):

| File | Load when... |
|------|-------------|
| [generated-doc-spec.md](resources/generated-doc-spec.md) | Writing AGENTS.md (Step 4) — for validation rules and formatting details |

**References** (guides and workflows):

| File | Load when... |
|------|-------------|
| principles (see repository README) | Evaluating quality or resolving tradeoffs |
| [incremental-update-workflow.md](references/incremental-update-workflow.md) | Running update mode |

---

## Now Execute

Proceed in the parsed mode. Remember: the output shape is orientation + gotchas.
When in doubt, cut it.
