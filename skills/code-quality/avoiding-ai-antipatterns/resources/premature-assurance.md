# Premature Final-Attestation / Speculative Completeness

Use this resource selectively when reviewing a plan, design, or agent workflow that
commits to final-form assurance before the implementation or evidence reveals what
must be distinguished. This is a diagnostic lens, not a required lifecycle, phase
model, or source of acceptance authority.

## Contents

- [Smell](#smell)
- [Diagnostic questions](#diagnostic-questions)
- [Finding threshold](#finding-threshold)
- [Default deny for new exactness](#default-deny-for-new-exactness)
- [Earned exactness](#earned-exactness)
- [Adaptive evidence sequencing](#adaptive-evidence-sequencing)
- [Calibrating no finding](#calibrating-no-finding)
- [Finding format](#finding-format)

## Smell

The artifact predicts the final evidence package too early and turns that prediction
into workflow law. Typical forms include:

- requiring an immutable commit, artifact digest, exact provenance chain, or complete
  signoff packet merely because work is called a release, publication, rollout, or
  scientific result;
- prescribing a fixed sequence of checks even when an earlier observation could
  identify which later proof matters;
- treating completion of forms, phases, counters, retry quotas, review labels, or
  polish grades as evidence that approved behavior is correct;
- requiring exact evaluated-snapshot binding before there is a consumer that needs
  to reproduce or act on that exact snapshot;
- letting a reviewer add new product requirements, redesign, speculative edge cases,
  or hardening and then treating them as inherited acceptance gates.

Distinguish a safety property from its preferred representation. Reuse the owning
tool's documented contract; justify an additional validation check by the concrete
failure it detects. Do not invent safety or validation requirements, or reject
otherwise valid output merely because its representation or metadata differs from
an agent's preferred form.

For example, a `0755` intermediate `.config` directory enclosed by owned private
`0700` directories, with a `0600` credential file, does not by itself establish
credential exposure. Requiring every intermediate directory to be exactly `0700`
would reject that layout without distinguishing a failure. Inspect effective
access and the applicable contract instead. Actual exposed credentials, unsafe
ownership or symlink/path handling, or a documented contract violation remain
reasons to stop and repair; do not mechanically weaken existing protections.

A detailed plan, broad validation, exact provenance, or immutable snapshot is not
itself a smell. The finding requires concrete evidence that the proposed commitment
is unsupported, non-discriminating, or acting as a proxy for the claim being made.

## Diagnostic questions

1. **Claim:** What behavior, invariant, or effect is the workflow trying to establish?
2. **Observation:** What is the least expensive discriminating observation available
   now? This means the least expensive observation that distinguishes the relevant
   failure possibilities, not the cheapest passing check.
3. **Adaptation:** Could that observation narrow, replace, reorder, or justify later
   evidence? If so, why is the plan fixing the later sequence in advance?
4. **Authority:** Did the user explicitly request this new exactness? A cited
   contract informs the risk assessment but cannot independently add a gate.
5. **Consumer:** Which current verified consumer requires the proposed snapshot,
   digest, provenance, field, label, or protocol, and why would semantic or
   behavioral proof be insufficient?
6. **Consequence:** What credible correctness or safety consequence follows if the
   exact form is absent or wrong? A plausible consequence can justify asking the
   user, but cannot by itself authorize a new exactness requirement.
7. **Gate authority:** Is a tool, reviewer, grade, label, checklist, or workflow phase
   being allowed to mint a gate independently of approved behavior and applicable
   contracts?
8. **Correction:** What is the smallest change that restores evidence-led sequencing
   without weakening a real invariant?

## Finding threshold

Report a finding only when the artifact provides concrete evidence of all applicable
parts:

- it mandates final-form evidence or a fixed validation sequence before the relevant
  uncertainty, consumer, or consequence is known;
- the mandate cannot itself prove the behavior or invariant it stands in for;
- following it would add avoidable work, hide an evidence gap, reject a valid result,
  or authorize acceptance without discriminating proof; and
- a smaller evidence-led sequence can preserve every applicable contract and safety
  boundary.

Skill selection, a P label, an A/A+ grade, a speculative edge case, a redesign idea,
or generic hardening does not mint an acceptance gate. Review prose becomes blocking
only when it proves approved behavior false, proves violation of an applicable
repository or external invariant or contract, or establishes a concrete credible
critical correctness or safety failure affecting the claimed behavior or effect.
A known critical bug is not polish and may not be deferred merely because a rubric
or review format labels it optional.

## Default deny for new exactness

Do not introduce a new exact commit-hash gate, byte-for-byte equivalence check,
artifact digest requirement, immutable provenance chain, or parity requirement by
default. Add one only when the user explicitly requests it. An existing contract or
credible consequence is evidence to bring to the user, not independent authority
for a new gate. Repository policy, reviewer, tool, model, grade, release label,
scientific label, reproducibility claim, audit convenience, or hypothetical future
consumer cannot mint one. Until requested, keep proposed exactness advisory; do not
expand the rubric, block the next observation, rebuild artifacts, regenerate
unchanged data, or couple unrelated identities.

Recording a commit, digest, byte count, or source identity as metadata is not the same
as making equality a gate. Prefer behavioral and semantic proof unless exact identity
is authorized. Reviewing the current patch or working-tree snapshot scopes which code
the evidence covers; it does not require committing every repair, hashing every
artifact, or enforcing byte parity between iterations.

## Earned exactness

Inventory existing exact evaluated-snapshot bindings and protocol, authorization,
idempotency, machine-owned byte, external-contract, destructive-effect, and safety
gates as removal candidates, even when their current consumer needs exact identity.
Do not mechanically remove them: identify the consumer and impact, then seek an owner
decision about replacement or retention. The explicit-request rule governs new gates.
Examples include:

- a signature or authorization check over exact bytes;
- an idempotency key consumed by a payment or mutation boundary;
- a deployment controller that installs only an attested artifact digest;
- a migration or destructive action whose approval is bound to a reviewed plan;
- an external protocol requiring exact field or acknowledgement semantics;
- acceptance evidence that would otherwise be collected against one snapshot and
  applied to a materially different one.

Do not infer those needs from the labels “release,” “publication,” “rollout,” or
“scientific” alone. An agent may not create a new exactness gate merely by naming a
consumer or consequence; it needs the user's explicit request.

## Adaptive evidence sequencing

When sequencing is useful, begin with the least expensive discriminating observation,
use its result to choose the next proof, and escalate breadth or cost only while an
unresolved claim or credible failure requires it. A quick check that can only pass the
happy path is not cheaper in the relevant sense when it cannot distinguish the
failure under consideration.

Check cheap local prerequisites before spending remote-call allowances. Repair a
diagnosed task-owned setup problem within approved scope and continue behavioral
validation without automatically seeking another approval or tearing everything
down. Stop for genuine scope, ownership, destructive-effect, or access conflicts;
do not blindly retry ambiguous or failed operations.

Do not convert this into mandatory external workflow state, a fixed phase taxonomy, a form,
required fields, time targets, counters, retry limits, or a ceremony budget. The
operational workflow that adopts adaptive evidence sequencing owns its execution;
this resource only diagnoses premature assurance commitments.

## Calibrating no finding

Do not confuse defects inside an earned control with premature assurance:

- **Earned gate with a bug:** a routing/readiness gate has a named consumer, but
  its prefix scan rejects a valid artifact. Report the correctness defect under
  the owning code review; the existence of the gate is not a Premature Assurance
  finding.
- **Digest-bound deployment:** a controller installs only the digest in a signed
  approval manifest and refuses changed bytes. Do not remove the existing digest
  check during review; inventory the deployment decision and ask the owner whether
  to retain it or replace it.
- **Defect-driven rereview:** review finds a concrete semantic defect, a focused
  repair fixes it, and targeted rereview stops. Review count alone does not make
  that adaptive sequence ceremony.
- **Consumer parity:** a producer artifact must pass the actual parser that will
  consume it. Preserve representative behavioral producer/consumer compatibility checks;
  producer-only checks become a Premature Assurance finding only when they are
  used to claim consumer compatibility before the consumer runs. That timing or
  proxy error is not automatically Heuristic Authority: report the sibling lens
  only when evidence is separately compressed or hidden and the summary gains
  downstream authority.
- **Later removal:** deleting an exact control later does not prove that it was
  previously unearned. Inventory plausible replay, audit, migration, or external
  consumers and ask the owner before changing their gates.

Return `INSUFFICIENT_EVIDENCE` only when a missing fact could flip the target
verdict—for example, whether a replay consumer exists. When the visible sequence
already proves an adaptive observation, focused repair, and pending final
acceptance, missing reviewer prose alone does not make the evidence insufficient.

## Finding format

A `FINDING` must state:

- **Source:** the exact plan or workflow commitment;
- **Claim:** the behavior, invariant, or effect it purports to establish;
- **Missing discrimination:** what the prescribed evidence cannot distinguish;
- **Unsupported authority:** the label, phase, tool, or attestation acting as a proxy;
- **Consumer/consequence:** the actual one, or evidence that none is named;
- **Smallest correction:** the next discriminating observation and how later evidence
  should adapt while preserving earned exactness.

If those facts are unavailable, ask a focused question or return no finding. Do not
replace one speculative assurance framework with another.
