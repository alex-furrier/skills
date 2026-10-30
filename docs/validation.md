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

Test built-wheel commands in a temporary environment so validation leaves installed tools untouched:

```bash
validation_dir="$(mktemp -d)"
uv venv "$validation_dir/venv"
uv pip install --python "$validation_dir/venv/bin/python" \
  packages/context-engineering/dist/context_engineering_cli-*.whl \
  packages/writing-check/dist/writing_check_cli-*.whl
"$validation_dir/venv/bin/context-engineering" --help
"$validation_dir/venv/bin/writing-check" --help
```

The repository tests also require a known Vale warning and a clean control through file, stdin, and sweep inputs. Successful startup or an empty alert list alone does not show that Vale checked the candidate.

The Writing Check package fetches its pinned Vale executable on first use through the pinned PyPI dependency. The repository does not provide a second setup command.

Check that the Claude projection is current before committing Context changes:

```bash
python scripts/project_context_plugin.py --check
```
