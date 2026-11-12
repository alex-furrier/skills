---
name: code-review
description: This skill reviews a branch or PR with proportionally selected review lanes, or checks prerequisites and executes a caller-selected profile. Use for direct review requests or when an owning lifecycle needs review execution without delegating repair, acceptance, or publication.
---

# Code Review execution facade

Execute one fixed review request after direct selection or caller handoff. Receive the repository, merge base, committed
candidate HEAD, selected profile, ordered lanes, approved-intent packet/digest,
and `prompt_contract_version` from the owning lifecycle. For caller-selected
requests, do not reselect the profile or specialist. Never modify code, calculate
acceptance, create a PR, or publish.

## Direct invocation

When no caller supplies a profile, select exactly one with the
[proportional review selector](references/proportional-review-selector.md).
Record selected and skipped lanes and their reason. Run
[preflight.md](references/preflight.md) before executing that fixed request,
using the evidence contract below. Gather repository,
merge base, committed HEAD and approved intent from the request and repository;
report missing material intent rather than inventing it. Record the prompt
contract used. A `deterministic-only` selection has no reviewer lanes: return its
proof and selection rationale without fabricating completed reviewer evidence.
When a caller supplies a profile, consume it unchanged.

## Early preflight

When an owner selects generic review during planning or delegation, follow
[preflight.md](references/preflight.md) before dependent work begins. Check only
the existing profile/lane contract and current execution prerequisites. Return
specific gaps to the owner; do not run reviewers, require a future candidate, or
persist completed review evidence. Recheck prerequisites at actual execution.

## Fixed request and result contract

Require the selected profile's exact ordered lanes. Preserve the existing lane
vocabulary: `diff`, `repository_fit`, `completeness`, and `bug_hunter`.
Persist one semantic result containing:

- repository, merge base, head, profile, ordered lanes, intent digest metadata, and
  `prompt_contract_version` (recorded scope, not proof of authorization);
- `executor` and `executor_contract_version`;
- typed findings and `correct|incorrect|unknown` correctness;
- timing/available usage evidence, durable artifact references, and explicit
  `completed`, `blocked`, or `unavailable` status.

## Execution

Require a fresh-context, read-only reviewer for every selected lane, launched
through the host's subagent or parallel-agent facility. If the full set cannot
launch, return `unavailable` with no completed lane evidence. Inline observations
may be offered as supplemental notes, labeled as such; they never satisfy a lane.
Give reviewers the committed diff,
approved intent, and repository rules, not the implementer's conversation or
self-assessment. Reviewers report findings; the owner verifies them and owns
repairs, acceptance, and publication.

Follow the [native subagent adapter](references/native-subagent-adapter.md)
for the existing ordered-lane evidence contract. Use an exposed native harness
route and record its actual executor identity and contract. Return the exact completion marker and
durable bundle; read that marker and its durable bundle rather than inferring completion from process age or a
digest lookup. Keep ancestor evidence labeled with its original HEAD and executor.

## Lifecycle boundary

Use this facade after validation when the execution owner selects generic
independent review. A direct `github-open-pr` invocation uses it when its caller
or the proportional selection requires that review. Deterministic-only ordinary
work does not need a synthetic review artifact or a formal acceptance packet.
When a caller or repository requires `implementation-acceptance`, this facade
returns evidence to that owner before publication. Missing required review is
still a blocker. `github-open-pr` owns CI, GitHub review, repairs, and PR readiness;
it does not convert readiness into formal implementation acceptance.

## Specialist questions

Select siblings only for a named question. Run each as a separate named-question
pass and read its artifact as the owner; these passes are not reviewer lanes.

- `code-health-review`: What raises maintenance and future change cost?
- `architecture-polish-review`: Are ownership and integration coherent?
- `avoiding-ai-antipatterns`: Does an abstraction or workflow add unearned complexity?
- `test-audit`: Which tests add little behavioral evidence or couple to implementation?

## Optional integrations

Treat `product-door-policy`, `product-experience-brief`, `skill-search`,
`github-open-pr`, and `implementation-acceptance` as optional external integrations
that may be absent from this catalog. If absent, record the question as unanswered;
do not require another missing skill as a fallback. When installed and selected,
publication and acceptance integrations may own those steps. Otherwise return
evidence to the repository owner without publishing or claiming acceptance. Use local files for
review evidence; no external evidence service is required.
