# Incremental Update Workflow

The update mode defaults to incremental updates rather than full bottom-up
reconstruction. This significantly reduces update time for typical repos.

## Algorithm

### Step 1: Assess Staleness

Run `uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering staleness <path-to-AGENTS.md> --json` to get a JSON report with:
- Last update commit and date
- Number of commits since
- Every changed path, its impact label (HIGH / MEDIUM / LOW), and the rule that produced that label
- Impact counts
- An advisory recommendation (`skip` | `partial-update` | `full-update` | `full-rebuild`) and its inputs

The impact labels and recommendation are navigation aids, not decisions. Read every
changed path and classification reason before choosing the update scope. Correct any
classification that does not fit the actual role of the file.

### Step 2: Choose Scope from the Evidence

Use the recommendation as a starting point:

| Recommendation | Scope to consider |
|---------------|-------------------|
| `skip` | Confirm the listed paths do not change documented behavior before reporting that docs are current |
| `partial-update` | Inspect the affected sections in Step 3 |
| `full-update` | Review all sections and update stale ones |
| `full-rebuild` | Consider a full quick-start scan while preserving accurate existing content |

Override the recommendation when the path-level evidence points elsewhere. Record the
chosen scope and why, including any classification or recommendation you overrode.

### Step 3: Targeted Section Updates

For each section of the existing AGENTS.md, check what changed:

| Section | Update when... |
|---------|---------------|
| WHY | README or project purpose changed |
| Commands | Package manifests, Makefiles, or CI workflows changed |
| Invariants | CI workflows, security configs, or build constraints changed |
| Gotchas | Common failure patterns changed (hard to detect — review if HIGH impact files changed) |
| Progressive disclosure | New AGENTS.md files created/removed, new docs/ files added |
| Frontmatter | Validate with `uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering frontmatter` — update if headings changed |

### Step 4: Diff-Based Editing

For each section that needs updating:
1. Read the current content
2. Discover the new reality (same discovery as quick-start, but only for that section)
3. Merge: keep accurate existing content, update stale parts, add missing parts
4. Do NOT rewrite sections that are still accurate

### Step 5: Validate

After updates:
1. Run `uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering frontmatter <target>` — check all frontmatter is valid
2. Run `uv run --no-config --locked --project <catalog-root>/packages/context-engineering context-engineering references <target>` — check all referenced paths exist

## Signals That Force Full Rebuild

Even in incremental mode, fall back to full scan if:
- The existing AGENTS.md has no recognizable structure (malformed or missing frontmatter)
- More than 50% of referenced paths no longer exist
- The repo has been significantly reorganized (many top-level dirs changed)
- User explicitly requests full rebuild

A `full-rebuild` recommendation is not itself a force condition. Confirm one of the
underlying conditions from the path-level evidence first.

## Report Format (Incremental)

In addition to the standard report, include:
- **Commits analyzed**: N commits since last doc update
- **Scope decision**: chosen scope, evidence used, and any advisory override
- **Sections updated**: list of which sections changed and why
- **Sections unchanged**: list of sections that were still accurate
- **Validation results**: output of frontmatter and reference checks
