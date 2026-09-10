# Fixture: stale module guidance

`AGENTS.md` says the module runs `make legacy-check`. The refactor replaced that target with `python -m module.verify`; `docs/` is now generated from checked-in templates. The requested work is an audit unless the prompt explicitly authorizes apply.
