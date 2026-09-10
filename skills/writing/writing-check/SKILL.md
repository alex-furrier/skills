---
name: writing-check
description: Run source-bound Vale checks and qualified readability sampling for exact writing candidates or repository-wide documentation sweeps. Use when auditing drafted prose or applying explicitly requested conservative repository writing updates.
---

# Writing Check

## Purpose and boundary

Collect deterministic, source-bound evidence for exact UTF-8 prose. Retain the source bytes, normalized findings, raw Vale output, and source identity. Results do not establish meaning, factuality, safety, usefulness, writing quality, acceptance, or readiness.

- Keep `writing_check.py` read-only. Do not add repository discovery, batch execution, network access, or an auto-fix path.
- A single-candidate check or repository audit never edits prose, source files, Git, or GitHub. Enter repository update mode only after an explicit request to update prose; the destination owner applies edits outside the checker.
- Never run `vale sync`, fetch a package, or use a network service during a normal check. Vale is required: when absent, retain source identity and return `unavailable`, never a substitute linter or clean result.
- Findings, readability, sample size, and counts are advisory observations, never scores or gates. Vale line and span values are Vale coordinates, not byte offsets.

The bundled, reviewed Google Vale v0.7.1 rules live in `vale/styles/GoogleDocs/`; their MIT license and upstream lock remain bundled. All severities are normalized to `suggestion`. `vale/profiles.json` is the authoritative profile inventory.

## Check one exact candidate

Locate this skill directory, inspect `--help`, and run:

```bash
python3 <skill-dir>/scripts/writing_check.py \
  --profile pr-description --json pr-body.md
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

Protected factual, safety, authentication, authority, command, and identifier text must remain byte-exact unless its real owner independently authorizes a factual change. This includes commands, identifiers, links, marker blocks, warnings, billing/authentication facts, and safety/authority language. A checker suggestion alone never authorizes paraphrase. In an edit workflow, the destination owner binds each fresh finding to the exact `source.sha256` and finding key as `fix`, `keep_exact_term`, `keep_quote`, `keep_required_text`, `keep_voice`, or `defer`. Discard it after any candidate change. This traceability is not a quality, readiness, or publication gate.

## Repository requests and policy maintenance

For a repository-wide request, load [repository-sweep.md](references/repository-sweep.md). Default to its read-only audit. Its update mode uses a shared three-pass rewrite budget, still invokes the checker one exact candidate at a time, and routes material edits to the named destination owners; unavailable owners permit only clear semantics-preserving fixes.

Normal checks are offline. Upgrade or calibrate vendored rules only in a reviewed change: fetch the named release to a temporary directory, verify the archive digest, show rule-by-rule diffs, update provenance and attribution, normalize severities, rerun `evals/rule-calibration.json`, and run the shared aggregate corpus once with complete expected-check reporting. Give contextual rules focused positive, negative, limitation/exact-term, and natural-prose fixtures, and record each imported rule’s known limitation.

Use retained evidence for audits. Produce replacement prose only when the user or destination owner requests it.
