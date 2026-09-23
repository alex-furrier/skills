# Deterministic documentation tests

Repositories can run the bundled verifier after a documentation change:

```bash
python3 <skill-dir>/scripts/docs_verify.py <target-repo-root>
```

It emits JSON. `context_cli: available` means the installed Context CLI ran the catalog frontmatter and reference checks. `context_cli: unavailable` exits nonzero: install the independently distributed Context CLI, then rerun; do not substitute another checker or a read-only inspection.
