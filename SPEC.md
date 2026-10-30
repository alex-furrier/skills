# skills specification

## Summary

`skills` is a portable catalog of engineering Agent Skills. It ships canonical skill instructions and the independently installable Context Engineering and Writing Check command packages.

## Goals / Non-Goals

- Goal: provide self-contained, redistributable catalog artifacts that work without a private checkout or personal configuration.
- Goal: keep deterministic Context analysis and source-bound Writing Check evidence available through their documented commands.
- Non-goal: make a hosted service, account, credential, private corpus, or personal automation a catalog prerequisite.
- Non-goal: treat advisory writing findings as proof of factuality, quality, or release readiness.

## Requirements

- Canonical skill sources MUST remain under `skills/`.
- The Context plugin MUST be an exact projection of its canonical skills and CLI package.
- Thinking MUST project exactly Blindspot, Research and Goalify from `skills/thinking/`; each is independently usable with no required model, provider or CLI. Product Bet Shaping MUST remain standalone outside Thinking.
- Each independently copied artifact MUST include the license and provenance needed for its declared boundary.
- Catalog validation MUST verify projection parity, provenance, packages, tests, documentation, and source formatting.
- Context analysis and Writing Check findings MUST remain advisory unless a named repository contract makes a result blocking.

## Interfaces & Contracts

- `context-engineering` — read-only Context analysis CLI packaged from `packages/context-engineering/`.
- `writing-check` — read-only, source-bound prose checker packaged from `packages/writing-check/`.
- `python scripts/fast_check.py` — repository validation entry point.
- `python scripts/project_context_plugin.py --check` — verifies the Context plugin projection.

## Invariants

- `plugins/context-engineering/` and `plugins/thinking/` are generated distribution artifacts, not second sources of truth.
- Provenance records cover every shipped file and copied third-party material has redistributable provenance.
- Release validation does not import personal Dots configuration.

## Acceptance

- `python scripts/fast_check.py` passes.
- `python scripts/project_context_plugin.py --check` and `python scripts/project_thinking_plugin.py --check` report current projections.
- The public command help for both packaged CLIs is available after the documented installation flow.
