# Canonical skills and projected Context plugin

Status: Accepted
Date: 2026-09-22

## Context

A skill-only install cannot rely on a sibling checkout for its required command. Earlier distribution layouts coupled Context skills to plugin-local code and left Writing Check with duplicate package material. PR #3 and PR #7 recorded the need for independently copyable artifacts while preserving one source of truth.

## Decision

Keep `skills/` and `packages/` canonical. Distribute Context Engineering through an independently installable package and a Claude plugin that is generated from the canonical Context skills and CLI package. Verify the projection with `scripts/project_context_plugin.py --check`. Keep Writing Check as its own self-contained package and skill.

## Consequences

Changes to canonical Context skills or CLI sources require regenerating and committing the plugin projection. The plugin remains a distribution artifact rather than an editable peer. Package-local license and provenance files remain required so copied artifacts preserve their declared boundary.

Evidence: [PR #3](https://github.com/safurrier/skills/pull/3) (merge `2a186eec714e57e390582f8c9e9d6aa0fe18c56d`, paths `plugins/context-engineering/`, `skills/context-engineering/`, and `packages/writing-check/`) and [PR #7](https://github.com/safurrier/skills/pull/7) (merge `4c46e8ca6637471f7bf1cc4a1091d0c0149b3e35`, paths `README.md`, `packages/context-engineering/`, `packages/writing-check/`, and `scripts/project_context_plugin.py`).
