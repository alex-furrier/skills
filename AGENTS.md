# Skills

The portable engineering catalog is the product. Keep the complete catalog self-contained, and declare any catalog-level package dependency directly in each affected skill. Keep skills read-only unless their contract names an explicit apply step and free of account, machine, credential, and private-corpus assumptions.

## Fast check

```bash
python scripts/fast_check.py
```

## Rules

- **DO** validate copied artifacts. **NOT** import Dots during tests. **BECAUSE** releases must work independently.
- **DO** record provenance for every shipped file. **NOT** copy unlicensed external material. **BECAUSE** publication needs redistributable inputs.
- **DO** keep findings advisory unless a named repository contract makes them blocking. **NOT** turn style output into a quality score. **BECAUSE** tools do not establish semantic correctness.
- **DO** prefer typed Python for repository automation. **NOT** add new shell scripts unless shell semantics are essential and Python would be materially worse. **BECAUSE** Python provides testability, structured failures, and static checking.
