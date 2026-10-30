# Skills

The portable engineering catalog is the product. Keep the complete catalog self-contained, and declare any catalog-level package dependency directly in each affected skill. Keep skills read-only unless their contract names an explicit apply step and free of account, machine, credential, and private-corpus assumptions.

Thinking sources live in `skills/thinking/`; regenerate `plugins/thinking/` with
`python scripts/project_thinking_plugin.py`. Product Bet Shaping is standalone
under `skills/product/`, outside that projection.

## Fast check

```bash
python scripts/fast_check.py
```

## Rules

- **DO** edit Context sources under `skills/context-engineering/` and `packages/context-engineering/`, then run `python scripts/project_context_plugin.py`. **NOT** hand-edit `plugins/context-engineering/`. **BECAUSE** the Claude plugin is a checked projection, not a second source of truth.
- **DO** validate copied artifacts. **NOT** import Dots during tests. **BECAUSE** releases must work independently.
- **DO** record provenance for every shipped file. **NOT** copy unlicensed external material. **BECAUSE** publication needs redistributable inputs.
- **DO** keep findings advisory unless a named repository contract makes them blocking. **NOT** turn style output into a quality score. **BECAUSE** tools do not establish semantic correctness.
- **DO** prefer typed Python for repository automation. **NOT** add new shell scripts unless shell semantics are essential and Python would be materially worse. **BECAUSE** Python provides testability, structured failures, and static checking.
