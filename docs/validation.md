# Reproducible validation

Run the complete repository check:

```bash
python scripts/fast_check.py
```

It validates provenance, package and plugin projections, skill links, package builds, tests, documentation, and source formatting.

Build the independent distributions with:

```bash
uv build packages/context-engineering
uv build packages/writing-check
```

Test clean-wheel command surfaces in temporary environments:

```bash
uv tool install --from dist/safurrier_context_engineering-*.whl safurrier-context-engineering
context-engineering --help
uv tool install --from dist/safurrier_writing_check-*.whl safurrier-writing-check
writing-check --help
```

The Writing Check package fetches its pinned Vale executable on first use through the pinned PyPI dependency. The repository does not provide a second setup command.

Check that the Claude projection is current before committing Context changes:

```bash
python scripts/project_context_plugin.py --check
```
