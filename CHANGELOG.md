# Changelog

## 0.1.0 — Unreleased

- Require `uv` and the catalog Context CLI for deterministic Context workflows; fail clearly when the complete package is absent.
- Restore reviewed Google Vale v0.7.1 policy assets for Writing Check, retain advisory findings, verify every vendored rule digest across both shipped copies, and ship MIT attribution and provenance.
- Support Writing Check as a self-contained skill while keeping the complete-catalog requirement for Context workflows.
- Fix Context CLI packaging and lock its development environment. Canonical `uv` commands ignore machine resolver policy and require the checked lock.
- Replace the shell release check with typed Python automation and add pinned Mypy validation.

Initial portable Context and Writing collection.
