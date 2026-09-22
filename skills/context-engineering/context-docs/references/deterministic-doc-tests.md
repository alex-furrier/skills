# Deterministic documentation tests

Repositories can run the bundled verifier after a documentation change:

```bash
python3 <skill-dir>/scripts/docs_verify.py <target-repo-root>
```

It emits JSON. `context_cli: available` means catalog frontmatter and reference checks ran. `context_cli: unavailable` exits nonzero: install the complete catalog with `uv` and `cli/`; do not substitute another checker or a read-only inspection.
