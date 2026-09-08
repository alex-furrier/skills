#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"; cd "$root"
# This is the full local release check, not a smoke test. It intentionally builds docs strictly.
uv run --python 3.11 --with pytest --with mkdocs pytest -q
uv run --python 3.11 --with mkdocs mkdocs build --strict
uv run --python 3.11 python scripts/validate.py
uv run --project packages/context-engineering context-engineering references . --json
# Writing Check findings are advisory, so a findings exit is valid release evidence.
uv run --python 3.11 python packages/writing-check/scripts/writing_check.py --profile technical-doc --json README.md || test $? -eq 1
git diff --check
