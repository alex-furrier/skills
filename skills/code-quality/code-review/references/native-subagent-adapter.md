# Native subagent review adapter

This is the native adapter for `code-review`; it executes an already
owner-selected request. It is not a selector, repairer, acceptance owner, PR
owner, raw-provider wrapper, or coordinator beyond collecting the ordered lane
outputs below.

`prompt_contract_version`: `native-subagent-adapter-v1`. Record this value in
the request and lane prompts; bump it whenever the fixed prompt changes.

## Contents

- [Preconditions and unavailable result](#preconditions-and-unavailable-result)
- [Native harness bindings](#native-harness-bindings)
- [Ordered lane execution](#ordered-lane-execution)
- [Lane judgments](#lane-judgments)
- [Aggregate and persist](#aggregate-and-persist)
- [Handoff](#handoff)

## Preconditions and unavailable result

Input is the immutable request: repository, merge base, candidate HEAD, profile,
ordered selected lanes, intent digest, and `prompt_contract_version`. Verify the
candidate HEAD before launch. Read committed files at that HEAD, not dirty
working-tree or mutable submodule contents; stop on candidate drift. Snapshot
nonempty approved intent once: approved behavior, deliberate tradeoffs, explicit
non-goals, and policy, never worker self-assessment. Require a fresh-context,
read-only reviewer for every selected lane, launched through the host's subagent
or parallel-agent facility. Keep reviewers separate from implementation context.
If the full set cannot launch, return `status: unavailable` with no completed
lane evidence. Inline observations may be offered as supplemental notes, labeled
as such; they never satisfy a lane.

The caller must treat `unavailable`/`blocked` as pre-mutation states. This
adapter never pushes, creates or edits a PR, posts a comment, or invokes an
unmanaged provider.

Use the caller-selected review directory, or for direct invocation default to
`${TMPDIR:-/tmp}/code-review/<repo>-<short-head>/` outside the repository.
For an unavailable or blocked run, write `<review-dir>/completion.json` with
`status: unavailable`, the reason, `started_at` if known (otherwise null), and
null `lanes_completed_at`, `aggregation_completed_at`, and `completed_at`.
This marker is not completed lane evidence.

Before launching children, record `started_at`. Completion must be observable
from artifacts rather than inferred from an interactive process. Do not treat a
TUI's age as execution time.

## Native harness bindings

Use the available host delegation interface. Record actual executor and contract
identity for each launched reviewer; return `unavailable` when the full set
cannot launch. Preserve requested role, model, effort,
access boundaries and read-only execution. Unsatisfied explicit requirements
remain blocked. Use tool-enforced read-only access when available; otherwise
instruct reviewers explicitly and reject results that violate the boundary.
Only the owner writes evidence artifacts.

## Ordered lane execution

For each lane in the supplied order, launch exactly one fresh native child with
read-only tools or an explicit read-only instruction boundary and this fixed prompt, replacing bracketed values literally:

```text
Prompt contract: native-subagent-adapter-v1.
You are the [LANE] lane of one independent code review. Read only the candidate
repository at [REPOSITORY]. Review [CHANGE_SOURCE]: either [MERGE_BASE]...[HEAD]
or supplied diff and changed-files paths for that exact range when git is unavailable. Do not write, select other
lanes, repair, accept, publish, use network providers, or infer work outside
this lane. Read [INTENT_PACKET] only as approved intent.

Use this lane JSON contract instead of any host reviewer's default output format.
Every finding requires `type`, `deduplication_key`, `lane`, `severity` (P0-P3),
`verified`, `path`, `line_range`, `title`, `body`, `evidence`, and `confidence` (0-1).
Return exactly one JSON object with `lane`, `execution_id`, `status`, and either
`artifact` or `result`, plus `findings` and `correctness`. `lane` must be [LANE];
`execution_id` must identify this child; `status` must be `completed`; use
`result:"clean"` when no artifact is needed. Every finding must use the common typed finding fields, including a non-empty stable lowercase-hyphen `deduplication_key` naming the violated invariant and required remedy. `diff` and `bug_hunter` may emit only `defect` or `question`; `repository_fit` may emit only `repository_fit` or `question`; `completeness` may emit only `completeness` or `question`. Use local correctness `incorrect` only when this lane
returns a verified `defect`; otherwise use `correct` or `unknown`. Do not claim
another lane ran. Apply scoped repository rules, citing only those that support
a finding. Report credible patch-introduced failures, not generic requests for
more tests or invented requirements.
```

## Lane judgments

Add only the selected lane's judgment to the fixed prompt. Do not rename,
merge, drop, or add lanes; run selected lanes in parallel when available.

- **`diff`:** Read every changed file and its full context. Report concrete
  patch-introduced correctness, security, validation, or maintainability defects.
  Missing tests qualify only for a specific changed behavior or failure scenario
  meeting the strict defect criteria, not generic test or hardening requests.
- **`repository_fit`:** Read applicable instructions and nearby canonical
  precedent. Report only repository-fit violations backed by a named canonical
  mechanism or instruction and a concrete consequence; invent no conventions.
- **`completeness`:** Compare the patch to approved intent. Report approved
  obligations missing a concrete consumer, registration, compatibility,
  migration, lifecycle, rollout, or cleanup edge. Generic requests for tests,
  docs, migration notes, and edge cases are not missing approved obligations.
- **`bug_hunter`:** Report only discrete, actionable patch-introduced defects
  that materially affect accuracy, performance, security, or maintainability,
  match repository rigor, and are something the author would likely fix. Do not
  rely on unstated intent; identify affected code when claiming breakage and
  exclude intentional changes. Prefer no finding to speculative noise.

Apply scoped rules in precedence order: `AGENTS.override.md`, `AGENTS.md`, then
configured fallbacks such as `CLAUDE.md`; more-specific guidance wins. Cite the
smallest supporting instruction range only when it adds material repository
scope, an invariant, remedy, convention, or confirmation behavior. Preserve rule
support when deduplicating; do not fabricate citations, omit ordinary findings,
or invent issues merely because an instruction file exists.

Use the following shared finding contract:
`type`, `deduplication_key`, `lane`, `severity` (`P0`–`P3`), `verified`, `path`,
`line_range`, `title`, `body`, `evidence`, and `confidence` (0–1). For example:

```json
{"type":"defect","deduplication_key":"reject-empty-input","lane":"bug_hunter","severity":"P2","verified":true,"path":"src/parser.py","line_range":"42-44","title":"Reject empty input before indexing","body":"Empty input raises IndexError instead of the documented result.","evidence":"parse([]) reaches items[0] at line 43.","confidence":0.95}
```

Use `question` with `verified:false` for unresolved evidence. Only verified
`defect` findings automatically affect correctness; other types need an existing
acceptance criterion to gate. Do not turn tradeoffs or non-goals into defects.

## Aggregate and persist

Require one parseable completed child object per ordered requested lane. Reject
missing, duplicate, reordered, unselected, blocked, or malformed lane results.
Record `lanes_completed_at` when the complete set arrives. Deduplicate findings only when their path/type match, line ranges overlap, and normalized violated-invariant/remedy `deduplication_key` tokens substantially overlap after generic remedy words are removed. Preserve the strongest severity/confidence result plus distinct corroborating body and evidence support. Preserve separate findings at one location when their keys differ. Child correctness labels are not the
aggregate verdict: derive aggregate `incorrect` only when the deduplicated set
contains a verified `defect`; otherwise use `correct` when every lane completed
or `unknown` when the evidence cannot support either claim. Aggregate in input
order as the common payload:

```json
{"findings":[],"correctness":"correct|incorrect|unknown","lane_results":[{"lane":"...","execution_id":"...","status":"completed","artifact":"..."}]}
```

Aggregate correctness is authoritative in both directions: `incorrect` requires a verified defect, and any verified defect requires `incorrect`. Each `lane_results` entry requires the
lane, child execution identity, `completed` status, and a durable artifact
reference or explicit `result:"clean"`. Write the consolidated non-empty
`review.md`, JSONL execution events (a locally generated adapter event is valid
when the native harness emitted no usage completion), and `findings.json`; then retain these files in the caller-selected review directory with a
`review-scope.json` recording the fixed request and executor identity.

After aggregate validation, record `aggregation_completed_at`; after durable
persistence and exact-reuse verification, record `completed_at`. Atomically
rename a temporary file to `<review-dir>/completion.json` containing those four
timestamps, status, durable bundle and output paths, model-call count, and
structured usage totals or explicit `unavailable` values. Write a completed marker
only after every named artifact validates; unavailable markers follow the rule above. The supervising owner monitors the
marker or a completion event, captures the outputs, and closes any idle
interactive process; it never substitutes session age for elapsed execution.

Return the durable bundle path, exact scope, selected native executor identity,
ordered lane results, completion marker, and status `completed` to the owning
lifecycle. Validate the complete evidence before returning it,
including any lane-result or artifact defect.

## Handoff

Return completed evidence only after checking the marker's status, requested
scope, and `durable_bundle`. Require nonempty `review.md`, `findings.json`,
`events.jsonl`, usage evidence, and `review-scope.json`; marker output paths must
resolve within that bundle and its scope must match the requested repository,
merge base, HEAD, profile, ordered lanes, intent metadata, prompt contract, and
native executor contract. A missing, malformed, blocked, or mismatched artifact
is blocked review, not a clean result. Return absolute marker and bundle paths,
review/findings/scope paths, exact reviewed SHAs, profile/lanes, and status to the
owner, then stop without repair or publication.

Keep artifacts outside the repository by default. When a caller explicitly
authorizes an in-repository handoff, retain the scoped diff, changed-file list,
commit log, and lane prompt records alongside the review evidence. Reviewers
remain read-only; the owner persists artifacts. Completion is evidence of
execution, not acceptance or an automatic PASS threshold.
