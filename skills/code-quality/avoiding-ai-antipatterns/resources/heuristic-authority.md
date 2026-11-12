# Heuristic Authority and Irreversible Semantic Compression

## Contents

- [Purpose](#purpose)
- [The smell](#the-smell)
- [When to inspect](#when-to-inspect)
- [Loss test](#loss-test)
- [Named-consumer test](#named-consumer-test)
- [Authority-boundary test](#authority-boundary-test)
- [Finding requirements](#finding-requirements)
- [Correction pattern](#correction-pattern)
- [Earned structure](#earned-structure)
- [Examples](#examples)

## Purpose

Detect designs that make an unproven heuristic, label, score, summary, or schema more authoritative than the evidence supports. The problem is not formal structure itself. The problem is allowing a lossy interpretation to replace source evidence or control behavior it cannot justify.

Use this review for code, implementation plans, technical designs, agent workflows, evaluators, schemas, protocols, and decision systems.

## The smell

**Heuristic authority** appears when a derived interpretation crosses from an advisory aid into a source of truth, required interface, or action gate.

The underlying mechanism is **irreversible semantic compression**:

1. Rich or ambiguous evidence enters the system.
2. A smaller category, enum, score, threshold, template, or normalized record summarizes it.
3. Downstream code treats the summary as authoritative.
4. Contradictory, revised, multi-valued, unknown, or source-specific evidence cannot survive or cannot be recovered.

A heuristic is not a finding merely because it is imperfect. Report a smell only when its authority causes concrete information loss, false precision, coupling, or unsafe behavior.

## When to inspect

Inspect this smell when a change introduces or promotes:

- a canonical enum or taxonomy over ambiguous observations;
- one required label where evidence can support several or none;
- a score or threshold that gates work without a calibrated consumer;
- a normalized record that discards raw values or provenance;
- a fixed template whose completion substitutes for task readiness;
- counters used as proxies for progress, quality, risk, or meaning;
- a model-facing tool that returns labels while hiding the source evidence;
- an internal hypothesis exposed as a public interface or persisted truth;
- a decision table that performs semantic judgment its inputs cannot prove.

Do not load this review for every typed schema, enum, parser, or deterministic state machine.

## Loss test

Replay concrete source cases through the proposed representation.

Ask:

> Do two source cases collapse to the same derived value even though a downstream decision could legitimately differ?

Also test whether the representation can retain:

- multiple simultaneous interpretations;
- `unknown`, unclassified, and disputed cases;
- contradictory observations;
- later corrections without overwriting history;
- original value, source, timestamp, and provenance;
- evidence that does not fit the proposed categories.

If a meaningful distinction disappears and cannot be reconstructed from the authoritative record, the normalization is lossy.

Do not accept “the raw data exists somewhere else” without verifying that the consumer and reviewing agent can reach it at the decision point.

## Named-consumer test

For every required field, state, threshold, or decision-table row, name:

1. the consumer;
2. the deterministic behavior that fails if the value is absent; and
3. why source evidence alone cannot satisfy that consumer.

Exact structure is usually earned for identity, signatures, digests, authorization facts, idempotency, acknowledgement and retry behavior, audit records, machine-parsed dependencies, and fail-closed lifecycle transitions.

Interpretive labels used only for routing, reporting, ranking, or reviewer convenience should normally remain derived, optional, or advisory. They must not independently authorize, suppress, remediate, erase evidence, or claim causality without supporting facts.

## Authority-boundary test

Treat the following transitions as review leads:

- advisory hint → hard gate;
- internal hypothesis → public interface;
- derived summary → source of truth;
- convenience label → authorization or suppression decision;
- provisional category → durable persisted state;
- model aid → replacement for evidence shown to the model;
- observed correlation → causal failure label;
- template or counter → proof of readiness or progress.

Name the exact transition in a finding. Do not report an abstract complaint about “overengineering.”

## Finding requirements

A valid finding must include:

- **Source evidence:** the observations or records being compressed.
- **Loss:** the concrete distinction, uncertainty, provenance, or revision that cannot survive.
- **Authority:** the action, gate, interface, or persisted truth controlled by the derived value.
- **Consumer:** the deterministic consumer requiring the structure, or evidence that none exists.
- **Consequence:** the wrong decision, false precision, hidden evidence, coupling, or unsafe behavior that follows.
- **Smallest correction:** the minimum change that restores evidence without weakening real machine or safety invariants.

Severity follows consequence, not the presence of a heuristic:

- **BLOCK:** the compression can authorize, suppress, corrupt, discard audit evidence, or violate an exact external contract.
- **WARN:** the design creates concrete coupling, false precision, or review/maintenance cost without immediate correctness harm.
- **NO FINDING:** exact structure serves a named deterministic consumer, preserves necessary evidence, and handles unknown or invalid states proportionately.

## Correction pattern

Prefer this split:

- Make the machine exact about facts it can verify.
- Preserve source evidence and provenance as the durable record.
- Keep semantic interpretation derived, versioned, replaceable, and reversible.
- Allow multiple, unknown, disputed, and revised interpretations where the domain permits them.
- Expose raw evidence with heuristic hints to an agent; do not return only the hints.
- Keep provisional internal categories out of public interfaces until a consumer and repeated evidence earn them.
- Fail closed at real trust boundaries rather than preserving semantic flexibility there.

A corrected design can contain more stored facts while making fewer unsupported semantic claims.

## Earned structure

Do not flag structure when all of the following hold:

- a named machine or safety consumer requires exact fields or states;
- invalid, missing, and unknown values have explicit behavior;
- source evidence or criterion-level proof remains available where later judgment needs it;
- the schema does not claim more semantic certainty than the consumer requires;
- removing the structure would break deterministic parsing, reconciliation, authorization, replay, or audit behavior.

Examples include signed event envelopes, content digests, idempotency keys, exact dependency URLs, fail-closed approval manifests, and bounded orchestration verdicts backed by retained criterion evidence.

## Examples

### Finding: preference summary replaces its evidence

A profile service turns several dated, conflicting user statements into one required `communication_style` value. Callers treat it as current truth, and the original statements are unavailable at response time. Preserve the observations and timestamps; make the summary derived and revisable rather than authoritative.

### Finding: estimated effort becomes a hard execution limit

A task runner estimates effort from changed-file count, then uses the estimate to impose a hard execution cap. The proxy controls termination even though file count cannot establish progress or risk. Bound the actual resource that requires containment and keep the estimate advisory.

### Clean: content-addressed artifact identity

A deployment system requires an artifact digest and rejects a release when the digest differs from the approved manifest. The controller is the named consumer, the digest preserves exact identity, and review evidence remains linked. The structure has earned its authority.
