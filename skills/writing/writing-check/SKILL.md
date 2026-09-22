---
name: writing-check
description: Run source-bound Vale checks and qualified readability sampling for exact writing candidates or repository-wide documentation sweeps. Use when auditing drafted prose or applying explicitly requested conservative repository writing updates.
---

# Writing Check

## Purpose and boundary

Collect deterministic, source-bound evidence for exact UTF-8 prose. Retain the source bytes, normalized findings, raw Vale output, and source identity. Results do not establish meaning, factuality, safety, usefulness, writing quality, acceptance, or readiness.

- Keep the installed `writing-check` command read-only. It remains single-candidate; do not add repository discovery, network access, or an auto-fix path.
- A single-candidate check or repository audit never edits prose, source files, Git, or GitHub. Enter repository update mode only after an explicit request to update prose; the destination owner applies edits outside the checker.
- Never run `vale sync`, fetch a package, or use a network service during a normal check. Vale is required: when absent, retain source identity and return `unavailable`, never a substitute linter or clean result.
- Findings, readability, sample size, and counts are advisory observations, never scores or gates. Vale line and span values are Vale coordinates, not byte offsets.

The `safurrier-writing-check` package bundles the reviewed Google Vale v0.7.1 rules, their MIT license, upstream lock, and a pinned Vale runtime dependency. From a checkout of this catalog, install it once with `uv tool install ./packages/writing-check`; then `writing-check --help` works without a second setup command. If the command is missing or returns `unavailable` or `execution_error`, report that state rather than running a substitute checker. All severities are normalized to `suggestion`.

## Check one exact candidate

Inspect `writing-check --help`, then run:

```bash
writing-check --profile pr-description --json pr-body.md
```

Pass a UTF-8 file or `-` for stdin. The public checker has no personal-voice option or bundled voice policy. A separately configured external overlay may run outside it; if unavailable, return portable evidence unchanged and use neutral prose rather than imitating a voice.

Choose a profile by purpose, not by the easiest readability outcome:

| Profile | Readability observation |
| --- | --- |
| `commit` | Disabled |
| `pr-description`, `user-facing-response` | Under 100 prose words or 5 sentences: insufficient; below 200 words or 8 sentences: small; otherwise advisory FRE 55 / FK 10 |
| `readme` | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10, or composition-limited |
| `technical-doc`, `technical-doc-explanatory` | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10 |
| `technical-doc-reference` | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10, or composition-limited |

All profiles use the reviewed Google Vale v0.7.1 observations. For every normal long-form sample, FRE 55 minimum and FK 10 maximum are advisory only. Reserve `user-facing-response` for its owner’s explicit plain-English rewrite; normal conversational drafting does not invoke Vale by default.

Readability includes paragraphs and blockquotes, link labels, and sentence-like list items with at least five words. It excludes headings, code, inline code, destinations and URLs, comments, raw HTML, frontmatter, table cells, images, and list fragments. README and reference profiles report `composition_limited` with no target when excluded table and fragment words outnumber prose. A table-dominated PR below 100 words or five sentences remains `insufficient_sample`. Do not publish targets by default.

## Interpret the record

The schema-v3 record retains decoded text, raw-byte length and SHA-256, selected public policy name and digest, sample state, raw stdout/stderr/argv/exits, and normalized alerts. It intentionally has no quality verdict, protected-span authorization, persistent exception, or aggregate score.

- `0` / `no_findings`: Vale ran and no configured pattern matched.
- `1` / `findings`: Vale ran and found one or more advisory patterns.
- `2` / `input_error`: source reading, UTF-8 decoding, or usage failed.
- `3` / `unavailable`: Vale could not be resolved.
- `4` / `execution_error`: version, execution, timeout, or JSON evidence failed.

Report `input_error`, `unavailable`, and `execution_error` explicitly; never convert them to `no_findings` or claim that a checker ran when it was unavailable.

Keep bytes exact only for a real exact-byte consumer: the candidate supplied to this checker and its `source.sha256`; policy, config, rule, and license integrity assets; machine-consumed command syntax and identifiers; and text the user or owning contract explicitly marks exact. Preserve the meaning, qualifications, and safety, authentication, authority, factual, and contractual constraints of all other prose; a checker suggestion alone never authorizes a factual or constraint-changing edit. In an edit workflow, the destination owner binds each fresh finding to the exact `source.sha256` and finding key as `fix`, `keep_exact_term`, `keep_quote`, `keep_required_text`, `keep_voice`, or `defer`. Discard it after any candidate change. This traceability is not a quality, readiness, or publication gate.

## Repository requests and policy maintenance

For a repository-wide request, load [repository-sweep.md](references/repository-sweep.md). Default to its read-only audit. A caller may run explicitly selected `{ "source": "…", "profile": "…" }` pairs in one process with `writing-check-sweep --candidates pairs.json --jsonl`; it emits independent unchanged schema-v3 JSON Lines records and never discovers candidates. Its update mode uses a shared three-pass rewrite budget and routes material edits to the named destination owners; unavailable owners permit only clear semantics-preserving fixes.

Normal checks are offline. Upgrade or calibrate vendored rules only in a reviewed change: fetch the named release to a temporary directory, verify the archive digest, show rule-by-rule diffs, update provenance and attribution, normalize severities, rerun `evals/rule-calibration.json`, and run the shared aggregate corpus once with complete expected-check reporting. Give contextual rules focused positive, negative, limitation/exact-term, and natural-prose fixtures, and record each imported rule’s known limitation.

Use retained evidence for audits. Produce replacement prose only when the user or destination owner requests it.
