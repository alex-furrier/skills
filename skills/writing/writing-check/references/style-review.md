# Contextual style review

Use these principles to review docs and PR copy, especially titles and lists
that readers scan together. Apply them where they help the reader; preserve
the different purposes of narrative, reference material, and comparable items.

1. **Make the actor and action clear.** Use a clear subject and verb, or start
   with the action when the actor is understood. Match tense to actual status;
   a proposed change must not sound deployed. Keep passive voice when the
   object matters more or the actor is unknown.
2. **Put distinct words first.** Lead with the problem, change, or outcome.
   Compare nearby headings or bullets: can readers tell them apart from their
   openings? Keep required headings and useful context. No fixed word limit
   applies.
3. **Use the same form and terms for like items.** Within a list or set of
   summaries, use one term for each concept and a stable sentence shape. Keep
   real distinctions and exact names. Do not force a template on all paragraphs.
4. **Make variation mean something.** Check whether extra length, emphasis, or
   detail in one item signals a real difference. Keep needed warnings, doubt,
   and exceptions. Do not force equal lengths or trim a unique risk for balance.
5. **Match verbs to purpose.** In feedback summaries, make praise and complaints
   easy to distinguish. In docs and PRs, use precise verbs that help readers
   spot failures, requests, and results. Keep neutral technical language when
   it fits; do not force praise or blame.

Preserve evidence and qualifications. A limited test cannot prove broad success.

For a useful finding, cite the passage, its effect on the reader, and the
principle. Otherwise leave the text alone. These judgments add no CLI matches,
scores, or gates. Keep the source identity with the review. Review again when
the text or its peer items change. This pass does not prove facts or readiness.

## Representative review cases

Use these made-up cases for a small manual check. In Audit mode, report the
problem without a rewrite. The edits below show authorized Draft/Improve work.

- **Repeated setup:** “This PR adds cache expiry. This PR adds retry limits.”
  → “Expire stale cache entries. Limit failed retries.” The openings now reveal
  the different changes (principles 1–2).
- **Term drift:** A document calls the same saved run a “session,” then a
  “conversation,” without a distinction. Choose its established term throughout
  (principle 3). Keep both terms if the system actually distinguishes them.
- **Hidden failure:** “Validation improved; malformed input still crashes.”
  → “Malformed input still crashes after the validation change.” The failure
  is clear without adding a claim about what tests proved (principles 2 and 5).
- **Meaningful exception:** Keep a longer migration bullet that explains data
  loss, even beside short setup bullets (principle 4).
- **Useful passive voice:** Keep “The signing key was revoked” when the key's
  status is what the reader needs and its revoker is unknown (principle 1).
- **Different roles:** Keep PR sections `Why`, `What changed`, `Risk`, and
  `Evidence`; they serve different purposes. Do not force identical sentence
  shapes across them or change required headings (principles 2–4).
