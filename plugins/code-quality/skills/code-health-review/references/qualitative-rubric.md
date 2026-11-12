# Qualitative Code Health Rubric

## Contents

- Cognitive overhead
- Locality and cold-reader onboarding
- Proportionality and earned complexity
- Evolutionary consequence
- Severity and heuristic authority

## Cognitive overhead

Ask how many new concepts, layers, modes, configuration points, dependencies,
and ordering rules a maintainer must carry.

Inventory concepts added, removed, and consolidated. Apply the deletion test to
new modules: if deletion makes complexity reappear across callers, the module
may be earning its interface; if complexity simply disappears, the module is
likely indirection.

Inspect whether callers must understand implementation details, lifecycle
ordering, hidden defaults, or several representations of the same fact. Do not
penalize a deep module merely for having a large implementation.

## Locality and cold-reader onboarding

Ask whether a developer unfamiliar with the feature can predict where it
belongs, find it from task or product language, and recover why it works.

Trace from the public ingress to the owning module, tests, configuration, and
architecture context. Record:

- number and relevance of file transitions;
- wrong turns caused by naming or placement;
- decisions duplicated across modules;
- tests that cross a different seam than callers;
- rationale available only in historical discussion;
- search terms from the task that fail to find the owner.

Use the 30-day test: could a bounded human or agent return after 30 days and
accurately predict behavior from repository evidence?

For a cold-reader trial, hide the author's file list and prior diagnosis. Give
only the repository plus task or PR intent. Treat navigation friction as
evidence, not as automatic proof of a code defect.

## Proportionality and earned complexity

Name the present problem before evaluating the solution. For each new
abstraction, mode, configuration value, extension point, or handled edge case,
identify the concrete requirement or observed failure that earns it.

Challenge:

- one adapter behind a generalized interface;
- flexibility with no named next consumer;
- exhaustive edge handling without credible consequence;
- framework construction where a direct implementation is reversible;
- migration scaffolding without a removal trigger;
- new policy surfaces duplicating an existing owner.

Also challenge false simplicity. A short function is not simple when it scatters
rules across callers or pushes failure handling outside the owning module.

Prefer deferring speculative flexibility when the direct solution is
reversible. Preserve exact structure for real identity, authorization,
idempotency, audit, dependency, and fail-closed lifecycle consumers.

## Evolutionary consequence

State what likely next change becomes easier and what becomes harder. Consider:

- change fanout and repeated edits across unrelated modules;
- whether a new invariant has one owner and one credible proof;
- whether extension follows an existing value axis or adds another branch;
- whether tests make later restructuring safer;
- whether the change reduces or increases reviewer reconstruction work.

Use later-change difficulty, rework, and cold-reader success as longitudinal
signals. Do not claim long-term maintainability from one green review.

## Severity and heuristic authority

Use `strong`, `mixed`, or `concerning` as advisory dimension judgments. Do not
aggregate them into a score.

Assign P0-P3 only when a file-grounded consequence exists:

- **P0**: unsafe correctness, data, security, migration, or lifecycle behavior.
- **P1**: major ownership or locality problem likely to cause follow-up bugs or
  make the change unsafe to evolve.
- **P2**: bounded polish that materially improves clarity, testability, or
  reviewability.
- **P3**: optional future cleanup with a named trigger.

For heuristic authority, require all of: source evidence, concrete information
loss, the authority granted to the derived value, the consumer, the resulting
consequence, and the smallest evidence-preserving correction. A metric crossing
a threshold is a review lead, not a finding.
