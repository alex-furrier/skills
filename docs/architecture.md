# Catalog architecture

The repository has one canonical catalog and three distributable command packages.

- `skills/` holds the canonical Agent Skill instructions. Writing skills are self-contained; Context skills declare the `context-engineering` package as their deterministic-analysis dependency. In Code Quality, only `code-health-review` declares a package dependency: `code-health`.
- `packages/context-engineering/`, `packages/writing-check/`, and `packages/code-health/` build the read-only `context-engineering`, `writing-check`, and `code-health` commands. `code-health` is published as `code-health-review-cli` 0.2.0 on PyPI.
- `plugins/context-engineering/` is the Claude marketplace artifact for Context Engineering. It copies the canonical Context skills and CLI source, then carries plugin-local license and provenance records.
- `scripts/project_context_plugin.py` is the only projection mechanism. Its `--check` mode compares the complete copied trees and required package files byte-for-byte.
- `scripts/fast_check.py` is the release-oriented entry point. It checks the projection, locked package environments, tests, strict documentation build, package behavior, provenance, evaluations, and whitespace errors.

The catalog does not require a hosted service, account, credential, personal configuration, or private corpus. GitHub and other external tools may enrich an individual skill workflow only when that workflow says they are optional.

See [installation](installation.md) for user-facing installation paths, [validation](validation.md) for the reproducible checks, and [the decision record](decisions/0001-canonical-skills-and-projected-context-plugin.md) for the source-of-truth boundary.
