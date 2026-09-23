# Catalog architecture

The repository has one canonical catalog and two distributable command packages.

- `skills/` holds the canonical Agent Skill instructions. Writing skills are self-contained; Context skills declare the `context-engineering` package as their deterministic-analysis dependency.
- `packages/context-engineering/` and `packages/writing-check/` build the read-only `context-engineering` and `writing-check` commands.
- `plugins/context-engineering/` is the Claude marketplace artifact for Context Engineering. It copies the canonical Context skills and CLI source, then carries plugin-local license and provenance records.
- `scripts/project_context_plugin.py` is the only projection mechanism. Its `--check` mode compares the complete copied trees and required package files byte-for-byte.
- `scripts/fast_check.py` is the release-oriented entry point. It checks the projection, locked package environments, tests, strict documentation build, package behavior, provenance, evaluations, and whitespace errors.

The catalog does not require a hosted service, account, credential, personal configuration, or private corpus. GitHub and other external tools may enrich an individual skill workflow only when that workflow says they are optional.

See [installation](installation.md) for user-facing installation paths, [validation](validation.md) for the reproducible checks, and [the decision record](decisions/0001-canonical-skills-and-projected-context-plugin.md) for the source-of-truth boundary.
