---
name: session-capture
description: "Extract durable knowledge from the current or a past agent session, propose ranked captures, and write only items approved in a subsequent user turn. Routes explicitly to the real owner: configured external knowledge destination, repo context, skill, task system, or one canonical owner plus an approved pointer. Use when the user says capture this session, what should we save, what did we learn, or write this down after productive work."
---

## Portable deterministic evidence

The Context CLI is a catalog-level optional dependency: run `PYTHONPATH=<catalog-root>/packages/context-engineering python3 -m context_engineering ...` when the package is installed with this catalog. A copied skill without that package must state `context_cli: unavailable`, preserve raw repository evidence, and continue only with read-only inspection; it must not claim the deterministic check ran or infer a replacement.

# Session Capture

Turn one session's non-obvious learning into durable knowledge without assuming
where it belongs. This skill owns discovery, proposal quality, the approval
boundary, and destination selection. The destination workflow owns the write.

## Public Boundary

| Intent | Owner |
|---|---|
| One current or past session; interactive proposals and writes | `session-capture` |
| Multiple sessions; batch repo-context pattern mining | a separate multi-session workflow |
| Reconstruct current engineering state for handoff | a configured state-checkpoint workflow |

Do not use a separate multi-session workflow as a second single-session entrypoint. Do
not merge current-state reconstruction into durable learning capture.

## Quickstart

1. Identify the current session or a supplied past-session artifact.
2. Extract evidenced, durable candidates.
3. Search likely owners and route each candidate.
4. Present ranked proposals and stop.
5. In a subsequent user turn, write only explicitly approved items through
   their destination owner.
6. Report exact changes or a no-change outcome.

For past-session formats and extraction rules, read
[`references/session-source.md`](references/session-source.md).

## 1. Extract Durable Signals

Scan the whole session, not only the final turns. Look for:

- validated workflows whose ordering or prerequisites mattered;
- debugging discoveries with symptom, root cause, and verified fix;
- non-obvious tool or API behavior;
- decisions with tradeoffs and reconsideration conditions;
- clarified mental models developed through back-and-forth;
- user corrections and re-explanations that should prevent repeated mistakes;
- pivots where an approach was abandoned after evidence changed;
- agent process failures whose remedy may be a workflow, task, context change,
  skill change, or explicit no-change/manual-review outcome.

Use only evidence present in the session or verified in the owning source.
Code changes alone are not durable learning; capture the understanding around
them. For agent-behavior episodes, use the non-exclusive fields in
[`references/capture-forms.md`](references/capture-forms.md#agent-improvement).

## 2. Find the Real Owner

Before proposing, search the plausible destination and existing artifacts.
Deduplication is a destination transformation before it is a content filter:

- propose `[Update]` when an existing owner has a real gap;
- propose `[New]` only when no appropriate artifact exists;
- filter out an item only when it is already fully documented or lacks durable
  value;
- when ownership is ambiguous, show the concrete alternatives instead of
  guessing from keywords, paths, or a score.

Use these explicit destination classes:

| Destination | Use when the durable value belongs to | Write owner |
|---|---|---|
| `external` | Personal or cross-repo knowledge | a configured knowledge adapter |
| `repo context` | Repo docs, ADRs, root or nested AGENTS.md | Repository workflow; read [`references/repo-context.md`](references/repo-context.md) |
| `skill` | A reusable behavior contract or an existing skill gap | the configured skill authoring workflow |
| `task` | Follow-up work rather than settled knowledge | Owning task file or tracker |
| `mixed` | One canonical owner needs a lightweight discoverability pointer | Canonical owner first; pointer only if separately approved |

Global agent behavior is not a separate destination class. In this managed
setup, global Claude, Codex, and Pi guidance comes from
`the configured global guidance source` or an owning skill, so propose `repo context` or
`skill` with that canonical source rather than editing generated runtime files.

The proposal must name the destination, primary target artifact, and every
required companion write such as an index or pointer. Give the primary target
the proposal's number and each companion a selectable suffix such as `1i`
(index) or `1p` (pointer). The user's approval, not an implicit router,
authorizes only the exact selected identifiers.

## 3. Propose Captures

Present a numbered list that previews enough content and routing for a real
decision. Use the relevant fields from
[`references/capture-forms.md`](references/capture-forms.md) so the user can
judge completeness before approval.

```text
Session: <repo or domain> — <task> (<date or today>)

Session produced N capturable items (M filtered out):

Core proposals:

1. [Update][repo context][Workflow] <title>
   Primary target [1]: <existing path>
   Companion target [1i, index]: <required index path, when applicable>
   Companion target [1p, pointer]: <optional pointer path, when applicable>
   Evidence: <what the session demonstrated>
   Preview: <steps, gotcha, or decision fields>

Possible extras:

2. [New][external][Decision] <title>
   Target: <proposed note or staging>
   Preview: <options, choice, rationale, reconsideration condition>

Filtered out:
- <candidate> — <already documented owner, transient detail, or other reason>

Capture all primary targets? Or pick exact identifiers, change a destination,
or make no changes.
```

`Capture 1` authorizes only primary target `1`; it does not authorize `1i` or
`1p`. `Capture 1 and 1i` authorizes those two exact writes. If the user names a
parent or range that does not map unambiguously to visible identifiers, ask
before writing. `Capture all` is defined shorthand for the exact set of visible
primary numeric identifiers; enumerate that resolved set before applying it.
Companion suffixes still require explicit identifiers.

Rank at most four high-signal items under **Core proposals**. Keep other
independently durable candidates under **Possible extras** with continuous
numbering. Normally target 3–7 proposals; consolidate closely related items
when there are more than seven. Do not invent automation, skills, or index
artifacts to pad recall.

Core signals include a named artifact with a specific gap, a reproducible
workflow with a trap, directly evidenced reusable agent behavior, and
non-obvious rationale likely to be revisited.

Always include `Filtered out`, including `none` when appropriate. A valid
outcome is no proposals and no durable change.

## Approval Gate

Every invocation is proposal-first:

- Reads, searches, and proposal generation are allowed before approval.
- Durable edits, notes, tasks, issues, branches, and PRs are forbidden before
  approval.
- Stop after proposals and wait for a subsequent user turn.
- Require an explicit action such as “capture all” (primary targets only), “do
  1 and 3,” or “write 1 and 1i.”
- A request to run the skill, enthusiasm, session completion, or silence is
  not approval.
- “Propose only,” “no edits,” or equivalent wording is a hard stop.
- If the user changes content or destination without approving it, show the
  revised proposal and continue waiting.

## 4. Apply Approved Captures

Apply only the approved exact identifiers, wording, and destinations:

- **external knowledge destination:** load a configured knowledge adapter. If unavailable, resolve the absolute
  configured configured external knowledge destination and use its `staging/` path; never write a relative
  `staging/`.
- **Repo context:** read
  [`references/repo-context.md`](references/repo-context.md), then follow the
  target repository's instructions, validation, and publication workflow.
- **Skill:** load the configured skill authoring workflow and edit canonical source, never only an
  installed or generated copy.
- **Task:** use the explicitly owning task system. Do not turn unfinished work
  into a knowledge note.
- **Mixed:** write the canonical owner, then only the separately approved
  pointer. Do not duplicate the full content.

If the user approves content but the destination remains materially ambiguous,
ask before writing.

If implementation discovers a required target that was not visible in the
approved proposal, stop and show a revised proposal. Do not treat approval of
the primary artifact as approval of a newly discovered index or pointer.

Preserve source context and approximate date. Do not copy credentials, secrets,
or sensitive internal links into a broader destination.

When rendering the approved content, preserve the relevant fields from
[`references/capture-forms.md`](references/capture-forms.md); adapt them to the
destination rather than forcing one note template everywhere.

## 5. Report

Name each created or updated artifact, its destination class, and what changed.
If nothing was approved or nothing cleared the durability bar, say so plainly.

## Quality Bar

- A future human or agent should benefit outside the exact session.
- Prefer stable understanding over volatile version trivia.
- A workflow normally needs at least three meaningful steps or one non-obvious
  ordering constraint.
- Preserve the user's terms and framing.
- Never fabricate missing evidence.
- Keep one canonical owner for mixed knowledge.
