# Selected review preflight

Run this check when an owner selects generic review, before implementation or
worker dispatch depends on it. Skip it when no generic review was selected.
This checks the existing contract and execution prerequisites; it does not run
review, approve the plan, or create a completed evidence record.

## Check the execution route first

Use the host's subagent or parallel-review facility. If it cannot launch the
selected independent lanes, return `unavailable`. Inline observations are
supplemental only and never satisfy a lane.
Record the available route and whether it can satisfy requested independence,
read-only access, model and effort requirements. If independence is required but
unavailable, return that unmet prerequisite; continue independent authorized work
without weakening selected review. Do not run paid canaries or live setup.

## Validate the selected contract

Keep repository verification profiles and generic review profiles distinct.
A repository's `check` and `verify` tasks are deterministic checks, not generic
reviewer lanes. Check the owner-selected profile and its exact ordered lanes:

| Profile | Ordered lanes |
| --- | --- |
| `full` | `diff`, `repository_fit`, `completeness`, `bug_hunter` |
| `bug-hunter` | `bug_hunter` |
| `repository-fit-completeness` | `repository_fit`, `completeness` |
| `bug-hunter-fit-completeness` | `bug_hunter`, `repository_fit`, `completeness` |

Require a nonempty `prompt_contract_version`, approved intent packet, exact
repository identity, and current commit IDs. Do not fabricate a future HEAD; a
planning-only snapshot has no final candidate and cannot yield completed review.
The selected route and ordered lanes are prerequisites, not proof of launch.
At execution time, the adapter validates the contract again before persisting.

Do not search unrelated evidence stores in preflight.
At execution, pass the exact `<review-dir>/completion.json` marker to the owner.
Check its status, `durable_bundle`, and output paths, then compare the returned
scope with the bundle's `review-scope.json`. Confirm the artifacts bind the same
committed candidate and native executor. A blocked or unavailable marker is not
completed evidence; never invent a private root or search for a different bundle
when a marker is missing.

Return the selected profile/lanes, route, and any unmet prerequisite to the owner.
Recheck changed prerequisites at execution time; never persist this preflight as
completed review evidence.
