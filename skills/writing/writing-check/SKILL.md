---
name: writing-check
description: Run source-bound Vale checks and qualified readability sampling for exact writing candidates or repository-wide documentation sweeps. Use when auditing drafted prose or applying explicitly requested conservative repository writing updates.
---

# Writing Check

Collect deterministic evidence only. Preserve the exact UTF-8 source bytes, normalized findings, and raw Vale output. A result does not establish meaning, factuality, safety, usefulness, writing quality, or readiness.

## Boundary

- Keep `writing_check.py` read-only. Never add repository discovery, batch execution, network access, or an auto-fix path to the checker.
- During single-candidate checks and repository audits, never edit prose, source files, Git, or GitHub.
- Enter repository update mode only after an explicit request. Apply edits outside the checker under the destination owner's authority.
- Never run `vale sync`, fetch a package, or use a network service during a normal check.
- Never turn findings, readability, sample size, or counts into a score or gate.
- Report Vale line and span values as Vale coordinates, not byte offsets.
- Let destination owners preserve commands, identifiers, links, marker blocks, warnings, billing/authentication facts, and safety or authority language.

Vale is a required Writing Check dependency. If it is absent, keep the source identity and return `unavailable`; never substitute another linter or report a clean result. The reviewed Google Vale v0.7.1 rules are bundled under `vale/styles/GoogleDocs/` with their MIT license and upstream lock. Every emitted severity is normalized to `suggestion`. `vale/profiles.json` is the authoritative profile inventory.

## Run

Locate this skill directory and inspect `--help`, then run one exact candidate:

```bash
python3 <skill-dir>/scripts/writing_check.py \
  --profile pr-description --json pr-body.md
```

Use a UTF-8 file or `-` for stdin. The public checker has no personal-voice option or bundled voice policy. A caller may use a separately configured external overlay outside this checker; when that owner is unavailable, return this portable evidence unchanged and use neutral prose rather than imitating a voice.

For a repository-wide request, load [repository-sweep.md](references/repository-sweep.md). Default to its read-only audit mode unless the user explicitly requests repository updates. Start from its complete ledger of unique tracked human-readable documentation instead of selecting only likely files. In update mode, use its shared three-pass rewrite budget to remove actionable findings and meet applicable readability targets before dispositioning residuals. Keep all checker invocations single-candidate and source-bound. In update mode, route material edits to the available destination owner: `readme-improver` for READMEs, `context-agents-md` for AGENTS files, `context-contracts` for specifications and ADRs, `context-docs` for structured docs, and `writing-core` for ordinary technical prose. When a required owner is unavailable, limit edits to clear semantics-preserving corrections and defer structure or meaning changes with a reason.

Profiles:

| Profile | Vale observations | Readability |
| --- | --- | --- |
| `commit` | Reviewed Google Vale v0.7.1 rules | Disabled |
| `pr-description` | Reviewed Google Vale v0.7.1 rules | Under 100 prose words or 5 sentences: insufficient; below 200 words or 8 sentences: small; otherwise advisory FRE 55 / FK 10 |
| `readme` | Reviewed Google Vale v0.7.1 rules | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10, or composition-limited |
| `technical-doc-explanatory` | Reviewed Google Vale v0.7.1 rules | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10 |
| `technical-doc-reference` | Reviewed Google Vale v0.7.1 rules | Normal at 300 words and 8 sentences; advisory FRE 55 / FK 10, or composition-limited |
| `user-facing-response` | Reviewed Google Vale v0.7.1 rules | Under 100 prose words or 5 sentences: insufficient; below 200 words or 8 sentences: small; otherwise advisory FRE 55 / FK 10 |

Apply the same FRE 55 minimum and FK 10 maximum to every normal-sample long-form profile while preserving each profile's sample-size and composition rules. Reserve `user-facing-response` for an explicit plain-English rewrite owned by the `user-facing-response` skill; normal conversational drafting does not invoke Vale by default. If that owner is unavailable, keep this checker read-only and return evidence only rather than drafting replacement prose.

Readability includes paragraphs and blockquotes, link labels, and sentence-like list items with at least five words. It excludes headings, code, inline code, destinations and URLs, comments and raw HTML, frontmatter, table cells, images, and list fragments. For README and reference profiles, report `composition_limited` with no target when excluded table and fragment words outnumber included prose. PRs below 100 words or five sentences remain `insufficient_sample` even when a table dominates. Targets are advisory observations, never public by default.

## Interpret structured evidence

The wrapper preserves exits `0` through `4`:

- `0` / `no_findings`: Vale ran and no configured pattern matched.
- `1` / `findings`: Vale ran and one or more advisory patterns matched.
- `2` / `input_error`: source reading, UTF-8 decoding, or usage failed.
- `3` / `unavailable`: Vale could not be resolved.
- `4` / `execution_error`: version, execution, timeout, or JSON evidence failed.

The schema-v3 record includes exact decoded text, raw-byte length and SHA-256, the selected public policy name and digest, sample state, raw stdout/stderr/argv/exits, and normalized alerts. It intentionally has no quality verdict, protected-span authorization, persistent exception, or aggregate score.

In an edit workflow, the destination owner must fix or explicitly disposition every finding for the exact source as `fix`, `keep_exact_term`, `keep_quote`, `keep_required_text`, `keep_voice`, or `defer`. Bind every disposition to `source.sha256` and the finding key. Discard it when the candidate changes; do not remap stale dispositions by location. This complete queue accounting is traceability, not a quality, readiness, or publication gate.

## Upgrade or calibrate

Normal checks are offline. Upgrade vendored rules only in a reviewed change: fetch the named release to a temporary directory, verify its archive digest, show rule-by-rule diffs, update authoritative provenance and attribution, normalize imported severities, and rerun `evals/rule-calibration.json`. Run a shared aggregate corpus once with its complete expected-check set; report unique fixtures, executions, and rule coverage separately. Give genuinely contextual rules focused positive, negative, limitation or exact-term, and natural-prose fixtures. Every imported rule records a known limitation.

Use the retained source and findings for audit. Do not produce replacement prose unless the destination owner or user requests it.
