---
name: product-bet-shaping
description: This skill turns a product idea, feature request, or possible workstream into a bounded evidence-backed bet recommendation. Use when deciding whether an idea is worth pursuing, what to prioritize, how to shape a bet, what outcome or ROI to measure, or whether to continue, park, reshape, or stop an existing initiative.
---

# Product Bet Shaping

Make the decision easier before making the project larger. Separate the user problem, intended outcome, evidence, funnel economics, alternatives, and opportunity cost; then recommend the smallest justified next commitment.

## Decision boundary

Produce a candidate bet; do not silently change the approved portfolio or existing commitments. Use the current priorities and constraints supplied by the user or available in authorized project context. Keep an interesting but unready idea separate from a recommendation to act now.

## Choose the mode

Use the lightest mode that can support the decision:

- **Triage:** Decide whether an idea deserves investigation at all.
- **Discovery:** Clarify the user, workflow, consequence, outcome, and missing evidence.
- **Shape:** Turn sufficiently supported evidence into a bounded bet.
- **Review:** Decide whether an existing bet should continue, reshape, scale, park, or stop.

Default to triage or discovery when evidence is thin. Do not write an implementation plan for an unselected problem.

## Workflow

### 1. State the decision

Write the decision as one sentence. Examples:

- Should this idea receive a bounded discovery pass?
- Should this workstream receive time or budget ahead of current commitments?
- Should the current bet continue after the first trial?

Name the decision owner and timing when known. Ask one focused question when the decision itself is unclear.

### 2. Decompose the request

Treat a proposed feature or system as a hypothesis, not the problem statement. Record separately:

- **Observed:** Concrete behavior, event, data, or prior commitment.
- **Consequence:** Time, money, risk, delay, frustration, or missed value.
- **Interpretation:** What the observations might mean.
- **Unknown:** What could materially change the decision.

Identify the person operating the workflow, the job they are trying to complete, and the most recent concrete instance. Prefer recent behavior and real workarounds over hypothetical enthusiasm.

### 3. Define the outcome before the output

Express the desired change in the user's situation. Avoid artifact-shaped outcomes such as “build a dashboard” or “ship an assistant.”

Distinguish:

- **Acceptance:** Did the implementation satisfy its contract?
- **Outcome:** Did the user's workflow or result improve?

Keep both when shaping delivery. Do not use implementation success as evidence of product value.

### 4. Map the whole funnel

Trace the path from available demand to realized value. Adapt this default:

```text
source demand
→ selected cases
→ eligible cases
→ attempted cases
→ technically successful cases
→ adopted or shipped cases
→ durable user or business outcome
```

For each transition, record:

- denominator and conversion when known;
- exclusion or failure reasons;
- model, infrastructure, review, correction, and operator cost;
- evidence quality and uncertainty;
- possible false positives and false negatives.

Do not report a conditional success rate as end-to-end impact. Separate efficient filtering from limited product coverage: rejecting unsuitable work cheaply may improve efficiency while still constraining total value.

### 5. Compare alternatives

Compare at least three responses when the decision is material:

1. the proposed approach;
2. a smaller, deterministic, manual, process, or non-AI alternative;
3. no action, delay, or investment elsewhere.

Reuse existing capabilities before proposing another platform. Do not force the answer to justify available infrastructure.

### 6. Form the investment case

Assess directionally rather than inventing a universal score.

**Potential value**

- severity of the consequence;
- recurrence and reachable volume;
- value per successful outcome;
- user or owner pull;
- strategic and career relevance;
- transferable learning or distribution.

**Likely cost**

- discovery and implementation effort;
- environment, data, and validation work;
- human review and supervision;
- ongoing operations and maintenance;
- coordination and adoption burden;
- opportunity cost and displaced focus.

**Confidence**

Label important claims as observed, inferred, or unknown. Treat rough ROI as a range or causal model, not false precision. State which missing fact could reverse the recommendation.

### 7. Select the smallest justified commitment

Choose one disposition:

- **Pursue now:** Evidence supports a bounded bet and it outranks displaced work.
- **Explore:** One short evidence-gathering step could change the decision.
- **Shape:** The problem is supported but scope, appetite, or risks need definition.
- **Park:** Potential value exists, but timing, ownership, or opportunity cost is unfavorable.
- **Stop:** Evidence or economics do not justify further attention.

For exploration, specify the smallest evidence step, time appetite, and stop condition. For a shaped bet, specify the problem, appetite, rough interaction, rabbit holes, exclusions, acceptance checks, and outcome check.

### 8. Protect the portfolio

Before recommending pursuit, answer:

- Which current bet would this displace?
- Why is switching now better than finishing the current commitment?
- Is this a durable workstream, a bounded probe, or merely a task?
- Who owns the outcome and ongoing operation?
- Who will provide ongoing analysis and operation, and is that burden justified?

When capacity is constrained, a good idea without a displacement case stays parked. If capacity is available, state that rather than inventing displaced work.

## Default output

Keep the first pass compact. Use the relevant parts of this outline; a short triage recommendation need not fill every section:

```markdown
## Bet read

**Decision:** [decision at hand]
**Recommendation:** [pursue now / explore / shape / park / stop]
**Confidence:** [high / medium / low, with reason]

### User and outcome
- Operator: [...]
- Workflow: [...]
- Desired outcome: [...]
- Current consequence: [...]

### Evidence
- Observed: [...]
- Inferred: [...]
- Unknown: [...]

### Funnel and economics
- Denominators and conversion: [...]
- Value path: [...]
- Cost and review burden: [...]
- Missing ROI evidence: [...]

### Alternatives
1. [...]
2. [...]
3. Do nothing or invest elsewhere: [...]

### Smallest next commitment
- Appetite: [...]
- Evidence or deliverable: [...]
- Stop condition: [...]
- Displaces: [current commitment or none]
```

Expand into a full pitch only after the first-pass recommendation earns it.

## Guardrails

- Preserve observations, consequences, interpretations, and unknowns as separate claims.
- Treat feature requests as investigation prompts, not specifications.
- Prefer deterministic evidence for machine-verifiable conditions.
- Require greater evidence for broader, costlier, or harder-to-reverse claims.
- Avoid scoring formulas that hide judgment or imply unsupported precision.
- Avoid architecture work when the unresolved question is demand, ownership, or value.
- Avoid broad research when one workflow walkthrough or data slice can change the decision.
- Do not equate interest, documentation, dashboards, or one successful run with adoption.
- Do not mutate task boards, approved priorities, external systems, or repositories without explicit authority.
