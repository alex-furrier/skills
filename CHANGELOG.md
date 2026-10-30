# Changelog

## 2026-10-30 — Portable Thinking and standalone Product Bet Shaping

- Adopt canonical Blindspot, Research and Goalify under `skills/thinking/`, each
  independently usable. Generate the three-skill `thinking` Claude plugin from
  those sources with copied-artifact, provenance and parity checks.
- Adopt Product Bet Shaping separately under `skills/product/`; keep Plan outside
  the bundle. Preserve original attribution and source hashes without private eval
  corpora, model selection, CLI dependencies or automatic activation.

## Writing Check CLI 1.0.1 — Unreleased

- Fix Vale stdin forwarding so it checks the retained candidate rather than a
  literal hyphen. Restore advisory warnings for file, stdin, and sweep inputs;
  preserve source identity, readability, policy, schema, and exit conventions.
- Require known-warning and clean controls through the packaged CLI's real
  pinned Vale runtime. Published install pins remain at 1.0.0 until release.

## 0.1.0 — Unreleased

- Make Writing Check's review order explicit: meaning, structure, and contextual
  style first, then automated diagnostics, justified revisions, semantic/style
  recheck, and a fresh check after text changes. Preserve justified residual
  findings without a blind rewrite loop; the CLI is unchanged.
- Add a contextual style pass to Writing Check reviews for docs,
  PR descriptions, and comparable text items. Keep semantic observations
  separate from the CLI's existing Vale and readability records.
- Give PR descriptions an explicit compact `Risk` section. Preserve the upstream
  assessment from the evidence pack, or report missing input as Unassessed;
  authoring does not rerun risk research or invent approval. Writing Check's
  lint profiles and the standalone risk skill are unchanged.
- Add standalone `pr-risk-note` and reuse it during PR-description drafting and
  improvement. Keep output to a risk label, advisory merge recommendation, and
  1–2 sentences; preserve unknown evidence and existing approval authority.
- Package Context skills and their shared CLI as one independently copyable Claude plugin, with plugin-local license and provenance records.
- Keep Writing Check as one self-contained skill, remove its duplicate package tree, and document separate Claude plugin and Skills CLI installation paths.
- Require `uv` and the catalog Context CLI for deterministic Context workflows; fail clearly when the complete package is absent.
- Restore reviewed Google Vale v0.7.1 policy assets for Writing Check, retain advisory findings, verify every vendored rule digest across both shipped copies, and ship MIT attribution and provenance.
- Support Writing Check as a self-contained skill while keeping the complete-catalog requirement for Context workflows.
- Fix Context CLI packaging and lock its development environment. Canonical `uv` commands ignore machine resolver policy and require the checked lock.
- Replace the shell release check with typed Python automation and add pinned Mypy validation.
- Add validated behavioral evaluation fixtures and simplify Context and Writing guidance while preserving commands, dependencies, ownership, and approval boundaries.

Initial portable Context and Writing collection.
