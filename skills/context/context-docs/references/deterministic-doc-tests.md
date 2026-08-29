# Deterministic documentation tests

Repositories can run the bundled verifier after a documentation change:

```bash
python3 <skill-dir>/scripts/docs_verify.py <target-repo-root>
```

It emits JSON. `context_cli: available` means catalog frontmatter and reference checks ran. `context_cli: unavailable` means an individually copied skill could not run those checks; preserve raw inspection evidence and report that limitation rather than substituting another checker.
