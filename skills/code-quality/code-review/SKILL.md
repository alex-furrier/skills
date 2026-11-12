---
name: code-review
description: This skill checks prerequisites and executes an already selected proportional code-review profile through independent native reviewers. Use when an owning lifecycle needs early review preflight or execution without delegating selection, repair, acceptance, or publication.
---

# Code Review execution facade

Execute one fixed review request. Receive the repository, merge base, committed
candidate HEAD, selected profile, ordered lanes, approved-intent packet/digest,
and `prompt_contract_version` from the owning lifecycle. Do not select a profile
or specialist, modify code, calculate acceptance, create a PR, or publish.

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

Use the host's subagent or parallel-review facility when available; otherwise review inline.
Keep each selected lane read-only and report whether execution was independent
or inline; inline review does not establish independent fresh-context evidence. Give reviewers the committed diff,
approved intent, and repository rules, not the implementer's conversation or
self-assessment. Reviewers report findings; the owner verifies them and owns
repairs, acceptance, and publication.

Follow the [native subagent adapter](references/native-subagent-adapter.md)
for the existing ordered-lane evidence contract. Use an exposed native harness
route and record its actual executor identity and contract. Return the exact completion marker and
durable bundle; read that marker and its durable bundle rather than inferring completion from process age or a
digest lookup. Keep ancestor evidence labeled with its original HEAD and executor.
If the request requires independence that inline review cannot provide, return
`blocked` or `unavailable` for that requirement, alongside any inline observations.

## Lifecycle boundary

Use this facade after validation when the execution owner selects generic
independent review. A direct `github-open-pr` invocation uses it when its caller
or the proportional selection requires that review. Deterministic-only ordinary
work does not need a synthetic review artifact or a formal acceptance packet.
When a caller or repository requires `implementation-acceptance`, this facade
returns evidence to that owner before publication. Missing required review is
still a blocker. `github-open-pr` owns CI, GitHub review, repairs, and PR readiness;
it does not convert readiness into formal implementation acceptance.

## Optional integrations

`github-open-pr` and `implementation-acceptance` may own publication and acceptance
when installed and selected by the caller. If absent, return evidence to the
repository's owner without publishing or claiming acceptance. Use local files for
review evidence; no external evidence service is required.
