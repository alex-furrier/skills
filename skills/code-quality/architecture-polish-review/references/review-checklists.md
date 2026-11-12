# Review Checklists

Use these prompts selectively based on the diff shape. Do not force every checklist onto every branch.

## Broad migration or lifecycle feature

- Name the branch-scale seams before listing findings: CLI/ingress adapter, application/lifecycle module, persistence/ledger, policy/readiness, side-effect adapters, rendering/output, compatibility/legacy surface.
- Propose a likely module/package map when one implementation file owns several concrete seams. Make the path from finding to extraction plan explicit.
- Ask what parity or characterization tests should exist before extraction. Good architecture cleanup often starts with a behavior baseline.
- For large refactors, order the rollout as: behavior baseline first, then one module seam per chunk, then focused validation after each chunk.
- Challenge compatibility mazes: does the branch expose one opinionated product interface, or multiple equal paths that future agents/users must choose between? Inventory public commands/options/docs and recommend removal or quarantine when the product direction is intentionally singular.
- Prefer extracting a real side-effect seam for locality/testability over inventing a plugin framework. One adapter can justify a side-effect seam when it isolates filesystem, process, network, credential, or external lifecycle behavior.

## Workflow-backed command or async user action

- Check whether the entrypoint acknowledges work before the workflow/queue has made an admission decision.
- Distinguish user-fixable validation errors from retryable infrastructure failures at workflow/activity seams.
- Compare behavior across all relevant ingresses/channel kinds, not just the one branch touched first.
- Check terminal rejection states: user-visible failures should usually be observable/metrical if similar errors are metered elsewhere.

## Generated adapters, setup snippets, or templates

- Treat generated/install scaffolds as first-class adapters when runtime behavior depends on them.
- Verify generated code preserves the interface expected by the deeper module, not just that the deeper module has pure tests.
- For lifecycle adapters, check that generated snippets preserve identity cardinality and ordering guarantees expected by reducers/state machines, such as one active id vs many active ids.
- Prefer tests that cross the same seam users install or invoke.

## Event hooks, lifecycle logs, and file-backed state

- Check lifecycle completeness: start without finish, finish without start, process exit without shutdown, duplicate events, restart with old state, stale process IDs.
- Require explicit proof of stale recovery for file-backed event logs: where are dead processes detected, tombstoned, or ignored?
- Check retention and replay cost: if events are appended and replayed, where does compaction/pruning/snapshotting live?
- Check stale-recovery efficiency: does implementation snapshot all processes on every hook/event, or only refresh candidate stale IDs?
- Keep stale recovery and compaction local to the bridge/materialization seam, not scattered across readers.

## CLI tools

- Inspect documented stdout/stderr/exit-code/JSON contracts against exceptional paths, not only happy paths.
- Check advertised flags, enum choices, and output formats for no-op behavior: each accepted choice should produce distinct documented behavior, be documented as an alias, or be rejected/removed.
- When command modules return structured result types, implementation exceptions should be translated at that module seam.
- For filesystem-writing tools, test hostile paths: parent path is a file, output path is not a directory, target exists, permission denied, dry-run avoids writes.
- Prefer non-mutating or locked validation modes when available. If a validation command updates lockfiles or local state, restore the working tree and report it as a validation caveat.

## Mutating external side effects

- If the diff adds writes, sends, uploads, mutations, or agent-triggered external side effects, inspect retry/idempotency semantics.
- For HTTP clients, check whether `POST`/non-idempotent operations are retried after ambiguous transport failure.
- Check whether files, streams, or generators can be replayed safely; if retrying after a response such as 429, ensure bodies are rewound or recreated.

## Validation reporting

- Separate branch findings from verification problems.
- If validation fails for an environment or pre-existing reason, report it as "verification blocked" rather than promoting it to a branch finding.
- Mark commands as run, skipped, or not applicable when that distinction matters.
