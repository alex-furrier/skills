#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; cd "$root"
# This is the full local release check, not a smoke test. It intentionally builds docs strictly.
uv run --python 3.11 --with pytest --with mkdocs pytest -q
uv run --python 3.11 --with mkdocs mkdocs build --strict
uv run --python 3.11 python scripts/validate.py
PYTHONPATH=packages/context-engineering uv run --python 3.11 python -m context_engineering references . --json
# Vale is optional: unavailable evidence is expected when it is not installed.
uv run --python 3.11 python packages/writing-check/scripts/writing_check.py --profile technical-doc --json README.md || test $? -eq 3
git diff --check
