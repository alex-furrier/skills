# Skills

Portable engineering skills are the product. Keep skills self-contained, read-only unless their contract names an explicit apply step, and free of account, machine, credential, and private-corpus assumptions.

## Fast check

```bash
./scripts/fast-check.sh
```

## Rules

- **DO** validate copied artifacts. **NOT** import Dots during tests. **BECAUSE** releases must work independently.
- **DO** record provenance for every shipped file. **NOT** copy unlicensed external material. **BECAUSE** publication needs redistributable inputs.
- **DO** keep findings advisory unless a named repository contract makes them blocking. **NOT** turn style output into a quality score. **BECAUSE** tools do not establish semantic correctness.
