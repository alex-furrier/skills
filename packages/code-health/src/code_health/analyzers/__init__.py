"""Concrete, fixed language adapter registry."""

from code_health.analyzers.go import prepare_golangci, run_golangci
from code_health.analyzers.python import run_ruff
from code_health.analyzers.rust import run_clippy
from code_health.analyzers.typescript import prepare_eslint, run_eslint

ADAPTERS = {
    "python": (None, run_ruff),
    "rust": (None, run_clippy),
    "typescript": (prepare_eslint, run_eslint),
    "go": (prepare_golangci, run_golangci),
}
