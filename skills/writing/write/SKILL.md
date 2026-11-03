---
name: write
description: This skill routes general requests to write, fix, or clean up prose through destination skills and advisory checks. Use when the user asks for writing help without naming a destination, or invokes write. Explicit PR descriptions, risk notes, READMEs, and response requests belong directly to their destination skills.
---

# Write

## Route by destination

Identify the audience, destination, and intended change from the request. Ask only
when a missing detail would change the draft. Read and follow the matching skill:

- PR body: [pr-description](../pr-description/SKILL.md).
- PR risk assessment: [pr-risk-note](../pr-risk-note/SKILL.md).
- Repository README: [readme-improver](../readme-improver/SKILL.md).
- Explanation, recommendation, or handoff to a user:
  [user-facing-response](../user-facing-response/SKILL.md).
- General prose: [writing-core](../writing-core/SKILL.md).

Honor an explicit destination request instead of adding a second writing workflow.

## Draft, review, finish

1. Follow the destination skill. Preserve facts, intent, and repository conventions.
2. If the draft reads synthetic, offer an optional
   [anti-llm-writer](../anti-llm-writer/SKILL.md) pass. Apply it only when requested
   or accepted, without weakening meaning.
3. Follow [writing-check](../writing-check/SKILL.md) on the exact final candidate,
   using its destination profile. Reuse valid evidence for unchanged bytes.
   Repair worthwhile findings and refresh checks after edits. Retain justified
   wording rather than chase a score. Findings stay advisory.
4. Return the requested prose with any material check limitation. Don't publish,
   post, or merge unless separately authorized.

Use the linked sibling skills only as needed. Follow Writing Check's setup for
its `writing-check-cli` package. If a sibling or checker is missing, report the
dependency and follow repository writing guidance. Never invent check results or
install tools without approval.
