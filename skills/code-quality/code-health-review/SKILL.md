---
name: code-health-review
description: "This skill reviews code health with deterministic metric deltas and qualitative judgment about cognitive overhead, locality, proportionality, and future change cost. It applies when the user requests a maintainability or project-health audit. It also serves as the default bounded health pass for medium and large code changes, while routine small changes skip it unless the user asks."
---

# Code Health Review

Use deterministic evidence to focus judgment. Do not turn metric counts,
holistic labels, or model interpretations into a quality score or automatic
gate.

## Select proportional coverage

Honor an explicit code-health, maintenance, AI-slop, or repo-health request at
any size. Never use `skip` for a direct request. Use the requested scope when it
is clear. If it isn't, use `focused` for a small or medium change and `thorough`
for a large or repo-wide audit.

For work without a direct request, use the changed behavior, its owner, and the
cost of the next change to choose the scope. Don't use raw file count, a generic
risk label, or the mere existence of a PR:

- **Skip:** a local fix, mechanical edit, doc or config update that doesn't
  change behavior, or other small change that keeps the same owner and seam.
- **Focused:** a medium feature or refactor. Run `diff` once on the narrowest
  coherent owning module that holds the changed code and its relevant tests.
  Apply all four review lenses to that path. Run a cold-reader trace only when
  the review says the code may be hard to find.
- **Thorough:** a large feature, broad refactor, migration, new subsystem, or
  cross-cutting change. Run `diff` once across the affected subsystem or repo.
  Check high-churn overlap, ownership, onboarding, and the cost of the next
  likely change.

Record `skip`, `focused`, or `thorough` in the plan or handoff. Cite the facts
behind the choice. CLI availability alone doesn't earn a pass for a small
change. Reuse evidence for the same candidate in architecture polish or
acceptance. Treat code-health evidence as advice. It creates no second approval gate
and can't replace tests or correctness review.

## Run the analyzer

Prefer the installed `code-health` command. Otherwise, define `CATALOG` as the
absolute path to a trusted checkout of this catalog repository. Obtain one with
`git clone https://github.com/alex-furrier/skills`, then set `CATALOG` to that
checkout. Run with the repository under review as the current directory:

```bash
uv run --frozen --no-dev --project "$CATALOG/packages/code-health" code-health diff . --base "$(git merge-base origin/main HEAD)" --format json
```

Pass the change's merge base, not a branch name that may already contain the
candidate. For one commit, pass `<sha>^`. Equal baseline and candidate revisions
produce a warning and `partial` status; they do not prove a clean committed diff.

The catalog package dependency is `packages/code-health` (Python 3.11+).
With explicit consent, install the [published Code Health Review CLI 0.2.0](https://pypi.org/project/code-health-review-cli/0.2.0/)
with `uv tool install code-health-review-cli==0.2.0`, then run `code-health --help`.
With explicit install consent, `uv tool install "$CATALOG/packages/code-health"`
remains a trusted source-checkout fallback. Never install automatically; if unavailable, report the deterministic
evidence gap and continue the qualitative review.

Use `scan` for a requested repository-wide snapshot without a baseline. Use
`diff` for a branch, pull request, or dirty working tree when a stable baseline
exists. Pass a nested path for focused coverage. Pass the affected subsystem or
repository path for thorough coverage. Avoid running both or widening a focused
pass merely to collect more evidence.

```bash
code-health scan . --format json
```

Treat unavailable analyzers as explicit evidence gaps. In a diff report,
`languages` describes the candidate scope. Findings from a language removed from
the candidate remain available only as resolved baseline deltas. Avoid installing
tools, modifying the repository, or inventing substitute values without user
authorization.

## Gather review context

Read the root and nearest scoped agent instructions, architecture records, and
tests for the touched paths. For branch review, inspect the merge-base diff and
PR intent. For periodic review, inspect current architecture and high-churn
hotspots.

## Apply the qualitative pass

Read [qualitative-rubric.md](references/qualitative-rubric.md). Judge:

1. cognitive overhead;
2. locality and cold-reader onboarding;
3. proportionality and earned complexity;
4. evolutionary consequence.

Use `strong`, `mixed`, or `concerning` for the four holistic dimensions. Keep
the labels advisory and attach file-grounded evidence.

Run a cold-reader trace when onboarding or discoverability is material. Start
from the task or product language without supplying the implementation files.
Record the path taken, wrong turns, missing context, and whether the owning
module and tests were predictable. Stop when the public ingress, owner, tests,
and rationale are found. After three distinct unsuccessful task-language search
pivots, stop and report the failed trace rather than touring the repository.

## Check heuristic authority selectively

Load the `avoiding-ai-antipatterns` heuristic-authority resource when the change
introduces a score, threshold, label, normalized record, template, or model
summary that controls behavior or replaces evidence.

Require source evidence, concrete loss, authority, a named consumer,
consequence, and the smallest correction before reporting a finding. Preserve
raw analyzer findings and provenance. Never let `strong`, `mixed`,
`concerning`, a count, or a future composite score authorize or block work.

## Report

Use this shape:

```markdown
## Code Health Review

### Verdict
<one short synthesis>

### Change shape
- Problem solved:
- Existing owner:
- Concepts added:
- Concepts removed or consolidated:
- Main execution path:

### Quantitative signals
- New or worsened hotspots:
- Resolved hotspots:
- High-churn overlap:
- Evidence gaps:

### Qualitative dimensions
- Cognitive overhead: strong | mixed | concerning — evidence
- Locality and onboarding: strong | mixed | concerning — evidence
- Proportionality: strong | mixed | concerning — evidence
- Evolutionary consequence: strong | mixed | concerning — evidence

### Findings
<P0-P3 findings only when a concrete consequence earns severity>

### What becomes easier or harder next
- Easier:
- Harder:
```

For an inline review, cite representative raw findings and preserve their tool,
rule, path, symbol, value, threshold, and availability. Do not enumerate every
finding when the complete JSON output already retains them. For a snapshot,
state that added and removed concepts are not assessed. Report dirty
working-tree paths because `revision` identifies `HEAD`, not the complete
filesystem state. Treat `non_test_lines` and `non_test_files` as broad active
source scope; they can include utilities, examples, or smoke harnesses and do
not claim deployment or runtime classification. Size metrics cover only the
requested scope, so tests elsewhere in the repository remain outside those
counts even when the qualitative review finds and inspects them.

Use P0-P3 only for concrete correctness, ownership, lifecycle, locality,
testability, or maintainability consequences. A concerning holistic dimension
does not automatically create a finding. Prefer no findings over generalized
advice.

Before completing the review, verify:

- the analyzer status and evidence gaps are reported;
- cited metrics retain tool, rule, location, value, and threshold;
- all four qualitative dimensions have file-grounded evidence;
- every P0-P3 finding names a concrete consequence independent of a threshold;
- every proposed abstraction has a present requirement, observed failure, or
  named trigger that earns it.

<!-- environment-specific-dependencies:v1 -->
## Dependencies and optional integrations

- **uv and Python 3.11+**: required for the source-checkout CLI route. Install `uv` through
  its upstream distribution. When unavailable, skip the CLI, report the
  deterministic evidence gap, and continue with the qualitative review.
- **Git**: installed by the host or operating system. Without Git, repository
  discovery and baseline/churn evidence are unavailable; report the gap and
  continue with the qualitative review.
- **Ruff**: installed separately for Python complexity findings. When missing,
  report Python analysis as unavailable and continue with other evidence.
- **Cargo and Clippy**: installed through Rust tooling. When missing, report
  Rust analysis as unavailable and continue.
- **ESLint 9 and `@typescript-eslint/parser`**: resolve both from the candidate
  workspace. The fixed external syntax-only configuration checks complexity,
  function length, parameters, depth, and nested callbacks. It never discovers
  repository config, performs typed/project analysis, fixes, downloads, or uses
  repository caches. Missing or incompatible local tooling is a TypeScript/
  JavaScript evidence gap.
- **golangci-lint v2 and Go**: resolve the executable locally. The fixed external
  config checks gocyclo, gocognit, funlen, maintidx, and revive argument-limit
  in disposable copies of the complete repository workspace, preserving local
  `go.work` and sibling-module context. They use readonly modules, isolated
  caches, and strict offline Go settings (`GOPROXY=off`, `GOSUMDB=off`,
  `GOTOOLCHAIN=local`). Missing dependencies or toolchains create an evidence
  gap instead of a download. The report preserves values and thresholds only
  for fixed, recognized v2 diagnostic forms (including maintidx's
  `Maintainability Index` output and
  funlen's separate line and statement diagnostics). Other approved-linter
  diagnostics retain `null` provenance rather than inferred numbers. Resolve
  focused paths to their owning module. Analyze repository modules
  deterministically or report an evidence gap rather than widening scope.

Treat all thresholds as advisory hotspot signals, not cross-language scores or
acceptance gates. Exclude dependency-cruiser, jscpd, `go list` dependency
analysis, duplication, typed TypeScript linting, automatic tool installation,
composite scores, and generalized analyzer plugins.

The skill remains useful as a qualitative review when the CLI or optional
analyzers are missing. Avoid hardcoding host installation paths.
