---
name: blindspot
description: "This skill improves a task's approach by researching missing domain knowledge externally, testing assumptions against local evidence, and applying relevant professional methods and prior art. Use when an answer or solution is plausible but shallow, an unfamiliar domain matters, or a different field could materially improve work such as MLOps, software design, diagnosis, UX, or creative practice."
---

## Portable execution

Use only available tools and authorized sources. Named research, web lookup,
planning and presentation helpers are optional integrations, not prerequisites.
When unavailable, investigate and synthesize directly with the available tools;
report missing evidence or procedures rather than inventing access or results.
Delegate only when the host supports it and the task authorizes delegation;
otherwise research inline. CLI and source-path examples illustrate methods,
not installed commands or permission to access a private repository. Adapt to
available source readers and cite the actual evidence. No model, provider,
account configuration, persistent destination or implementation permission is
selected by this package. Blindspot remains experimental.


# Blindspot

Improve the approach to the task with relevant expertise and evidence. Seek a
better method or a missing insight, not a larger project or a performance of
expertise. Apply the useful findings to the actual work.

## Recognize what is missing

Start from the user's task, supplied context, and existing work. Identify the
outcome or decision being served and the uncertainty that limits progress.
Check whether the proposed solution already assumes its cause: retraining may
assume model drift; a redesign may assume interface confusion.

Look for consequential gaps in domain knowledge, raw evidence, methods, tools,
constraints, or ways of judging the result. Ask what a competent practitioner
would inspect or do that the current approach omits. Consider an adjacent field
when it exposes a real blind spot; a single relevant specialty can be enough.
Reframe the task only when that helps its intended outcome. Preserve scope,
constraints, and the chosen objective rather than replacing them with a more
ambitious project. Clarify only a missing answer that could change the work.

Distinguish an unclear intention from a gap in expertise. Use `goalify` when a
compact intent synthesis would help; ask the user only about preferences or facts
they can supply. Do not ask them to provide the professional knowledge this pass
is meant to discover. Research can precede and change the goal synthesis. Skip
this pass for an understood local fix or settled mechanical task unless a named
uncertainty could change its approach.

## Find and use the relevant expertise

Research the gap with available, authorized sources. When consequential domain
expertise is missing, actually consult external primary or practitioner material;
do not substitute recalled best practices for research. Inspect the underlying
passage, demonstration, or implementation. Reuse already inspected material when
it answers the gap; do not repeat a lookup for appearances. If access fails,
state the unresolved gap and narrow the recommendation rather than implying it
was researched.

Apply local expertise where the answer depends on a repository or operating
context. Find the relevant skills, domain docs, current consumers, and comparable
implementations. Follow a promising precedent through focused Git history, PR
descriptions/reviews and design rationale, then relevant follow-up fixes or reverts.
Use that trail to understand why an approach fit, what it cost, and where it failed.
A merge shows acceptance, not sustained success: distinguish tests, review claims,
continued use and observed outcomes, and say when outcome evidence is unavailable.

Identify knowledgeable owners or reviewers from relevant contributions and
recorded reasoning, not popularity or commit counts alone. Treat them as potential
context sources; inspect their available work and do not initiate outreach without
explicit user authorization. Search only authorized project sources. Follow the
few leads that could change the decision, not every category on every task.

Look broadly enough to challenge the initial framing without requiring a roster
of disciplines, a famous practitioner, or a fixed number of sources.

Find actual expertise in primary documentation, papers, reference implementations,
standards, practitioner demonstrations, postmortems, and comparable work. Identify
real practitioners or teams when their methods matter; inspect their work rather
than inventing what an expert would say. Follow promising secondary leads to the
underlying artifact. Inspect the relevant passage, behavior, or implementation;
search snippets and prestige alone cannot support a recommendation.

For open design questions, canvass a few strong domain exemplars or nearest
analogs. Inspect concrete workflows or implementations, not just product claims.
Extract the characteristics that make each useful here, a meaningful tradeoff,
and what would fail if copied into this context. Use mature products as leads,
not proof that their design caused success. Let these observations inform what
good means; do not impose an exemplar quota or replicate their whole feature set.

Extract the useful method: what material it starts with, what it does, which
constraints matter, and how its result is checked. Apply or adapt it to the local
problem. Explain why the transfer fits and where it might fail. Compare existing
solutions, reuse, or a simpler approach when that choice is open; do not force an
alternatives exercise for a settled decision. Check suitability and permission
before recommending concrete code or asset reuse.

Keep factual claims traceable to inspected sources. Separate observations and
reported claims from inferences, assumptions, and proposals. Seek contrary
evidence for a consequential claim; repeated copies of one account are not
independent support. State inaccessible evidence and its effect on the conclusion.
Never imply having measured, run, watched, or interviewed something only described
in text. Do not fabricate expert agreement or simulate a panel.

## Turn findings into what good looks like

Translate consequential findings into a small set of context-specific signs of a
good result: what must work for this user, which tradeoff matters, and what would
expose a misleading success. Explain the evidence behind a criterion and the local
inference needed to apply it. Keep unresolved preferences and empirical questions
visible; expert practice alone does not establish this user's priorities. When
external guidance and local precedent disagree, compare their versions, operating
assumptions and constraints. Explain which applies here, the tradeoff it implies,
and what remains unresolved rather than treating either source as automatic authority.

Prefer criteria that change a choice or reveal a failure over generic qualities
such as robust, intuitive, or production-ready. Do not manufacture metrics, an
exhaustive rubric, or an evidence ledger. A sentence can be enough. Revise an
initial goal when research exposes a consequential missing need, without treating
an adjacent opportunity as permission to expand the work.

When research materially changes or clarifies the goal or a consequential success
criterion, make a short provisional goal and its decisive tradeoff visible in the
working conversation before expanding the plan. Use `goalify` when available; the
task owner should show its returned synthesis to the user, rather than leaving it
only in private research or the final plan. State what the user should be able to
do, the cost or limit they would accept, and any material preference still assumed.
Keep supporting research available through concise links. Continue independent
authorized work; ask at most one material question and pause only work that depends
on its answer. Reuse feedback and skip this checkpoint when intent and criteria are
already settled. If `goalify` is unavailable, make the same compact synthesis directly.

When research and planning already have separate owners, use the
[handoff pattern](references/feedback-handoff.md) before starting the planning owner.

## Improve the work and stop at a useful answer

Use the findings to change or strengthen the actual decision, diagnosis, design,
implementation approach, or explanation. Make the connection visible: which
assumption changed, which technique became useful, or why the initial approach
survived scrutiny. A bibliography or vocabulary upgrade is not the result.
If research adds nothing material, say so and retain the adequate approach.

Choose evidence of correctness or usefulness appropriate to the claim: inspected
source, an architecture argument with explicit tradeoffs, a reproducible test,
representative benchmark, incident trace, domain review, or observed user behavior.
Propose an experiment or prototype only when an empirical uncertainty needs it;
do not append one to every answer. Execute only within the user's scope. Do not
confuse a proposed check with a result, or a convenient proxy with the desired
outcome. Note what would change the decision when material uncertainty remains.

Scale effort to unfamiliarity, ambiguity, cost of error, and available time.
A narrow question may need one authoritative reference and a corrected answer;
a consequential unknown may need deeper investigation. Count research and any
construction or validation against the total budget. Stop when the task is
adequately supported, the next useful observation requires different access or
execution, further searches repeat the same evidence, or the budget is reached.
Return the best supported result and remaining uncertainty rather than extending
the research to fill a template.

Use the output form the task needs. Explain the useful change and its evidence
concisely; do not require a separate brief, source cards, plan, or report. Save or
publish only to a requested destination.

## Work with existing owners

Use this as an approach-improvement pass within the current task. Keep `research`
as the owner of substantial factual investigation and evidence verification;
`openai-web-research` can supply a public-web lookup. Keep implementation planning
with `plan`, diagnosis with the debugging owner, evaluation with the relevant
eval skill, and design with its product/UX owner. Pass useful findings into their
existing output rather than restarting the task or copying their workflows.
If a helper is unavailable, use the available evidence within its limits and
continue the authorized task; do not require installing a workflow stack.

For article attribution and the limits of our development evidence, read
[references/origin.md](references/origin.md) when explaining the approach.

<!-- environment-specific-dependencies:v1 -->
## Environment-specific dependencies

Classify as **portable**. Require no particular model, provider, CLI, or private
service. Use available reading, search, and analysis tools. When sources or raw
evidence are unavailable, state the limit and narrow the conclusion; do not invent
access, install tools automatically, or present an unverified result as established.
