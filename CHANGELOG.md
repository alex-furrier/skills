# Changelog

## Code Health scan consistency and lightweight Cargo copies

- Port a fix already merged in a downstream vendored copy of this plugin
  (merge `99dfe87e`).
- Run both ESLint snapshots with the same external configuration and relative
  targets; treat unmatched configuration as missing evidence, not a clean scan.
- Exclude caches, environments, `node_modules` and `target` from Cargo copies.
  Keep vendored dependencies and Rust inputs in `build`, `dist`, `archive` and
  `_archive` directories, with isolated build output. Add regression coverage.
- Keep package 0.2.0 and marketplace plugin 0.1.0 unchanged: this is not a release,
  and the canonical plugin does not bundle the CLI.

## Code Health Review CLI 0.2.0 — published install guidance

- Pin the published `code-health-review-cli==0.2.0` install in the README,
  installation guide, and Code Health Review skill; retain explicit consent,
  the trusted source-checkout fallback, and the no-automatic-install rule.
- Record the release and successful clean install, update architecture guidance,
  and regenerate the Code Quality plugin from the canonical skill.

## Code Health Review publishing preparation

- Add a release-triggered trusted-publishing workflow for `code-health-review-cli`
  0.2.0, with tag identity and archive validation before publishing.
- Keep source-checkout installation documented until the first PyPI release.
  Clarify that Code Quality findings support human judgment, not verdicts.
- Include the review-plugin projection command in contributor instructions.

## Claude marketplace — Code Quality and Writing

- Add generated `code-quality` and `writing` plugins at version 0.1.0 to the
  marketplace, with copied canonical skills, licenses and provenance.
- Check projection parity in fast check. Keep companion CLIs separate: Code
  Health Review retains its installed-command or trusted-checkout fallback.

## 2026-11-12 — Portable Code Quality suite and code-health CLI

- Adopt Code Review, Code Health Review, Architecture Polish Review, Avoiding AI
  Antipatterns and Test Audit under `skills/code-quality/`, with source hashes
  and without host-specific reviewer bindings, managed evidence services or
  private paths. Review judgments, profiles, lanes and finding rules are unchanged.
- Let Code Review select one proportional review profile itself when invoked
  directly; a caller-selected profile is still consumed unchanged.
- Add the `code-health` CLI (`code-health-review-cli` 0.2.0) under
  `packages/code-health/`. It is not published to PyPI; run it from a source
  checkout. Fast check runs its tests, lock check and independent wheel install.

## 2026-10-30 — Portable Thinking and standalone Product Bet Shaping

- Adopt canonical Blindspot, Research and Goalify under `skills/thinking/`, each
  independently usable. Generate the three-skill `thinking` Claude plugin from
  those sources with copied-artifact, provenance and parity checks.
- Adopt Product Bet Shaping separately under `skills/product/`; keep Plan outside
  the bundle. Preserve original attribution and source hashes without private eval
  corpora, model selection, CLI dependencies or automatic activation.

## Writing Check CLI 1.0.1 — 2026-10-30

- Fix Vale stdin forwarding so it checks the retained candidate rather than a
  literal hyphen. Restore advisory warnings for file, stdin, and sweep inputs;
  preserve source identity, readability, policy, schema, and exit conventions.
- Require known-warning and clean controls through the packaged CLI's real
  pinned Vale runtime. Published install guidance now pins the verified 1.0.1 release.

## 0.1.0 — Unreleased

- Require a usable, source-bound README checker record in repository validation.
  Findings remain advisory; import crashes, empty output, stale source identity,
  and error records can no longer pass merely by exiting 1.

- Review canonical documentation with the corrected Writing Check runtime. Clarify
  installation conditions, isolated validation, and historical evidence without
  changing authority boundaries or forcing advisory findings to disappear.

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
