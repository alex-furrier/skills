# Capture forms

Use only the form that matches the evidenced learning. These are completeness
prompts, not mandatory headings for every destination.

## Workflow

- context: when and why to use it;
- prerequisites;
- numbered steps in their validated order;
- commands or code that matter;
- gotchas, including failed-looking alternatives;
- source task, repository, and approximate date.

## Debugging discovery

- observed symptom or error;
- root cause;
- verified fix or workaround;
- why the obvious approach failed, when known;
- scope or conditions under which the result applies.

## Decision

- options considered;
- criteria and constraints;
- chosen option and rationale;
- tradeoffs accepted;
- conditions that should trigger reconsideration.

## Tool or API knowledge

- tool and relevant version or environment;
- non-obvious configuration, flag, or behavior;
- obvious attempt and why it failed;
- working example;
- source task, repository, and approximate date.

## Concept clarification

- concept and domain context;
- initial ambiguity or misunderstanding;
- clarified mental model;
- nearby concepts that are easy to confuse;
- limits of the explanation established by the session.

## Agent improvement

- episode type: correction, re-explanation, pivot, repeated pattern, blocker,
  or process failure;
- what happened and what evidence changed the approach;
- likely cause, preserving uncertainty: missing context, domain gap, workflow
  gap, process failure, or unclear;
- source citation or session identifier;
- zero or more plausible destination owners with free-text rationale;
- counterevidence or recurrence needed before encoding;
- explicit no-change/manual-review option.

Do not force a composite episode into exactly one target. One correction may
simultaneously expose a repo invariant, workflow gap, and process failure.
Preserve the source episode and let the approved encoding step resolve which
owners, if any, should change.
