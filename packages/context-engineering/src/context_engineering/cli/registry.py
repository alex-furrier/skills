"""Subcommand registry — one dataclass per subcommand, zero dispatcher boilerplate.

Each subcommand declares:
- its name, help text, and Examples block
- a `configure(parser)` callback to add arguments
- a `run(args) -> Result` callback — the actual handler

`dispatch.main` walks the registry to build the parser, pick a handler, and
render the result uniformly.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Configure = Callable[[argparse.ArgumentParser], None]
Run = Callable[[argparse.Namespace], Any]  # Returns LintResult | AnalysisResult


@dataclass(frozen=True)
class Subcommand:
    name: str
    help: str
    description: str
    examples: tuple[str, ...]
    configure: Configure
    run: Run

    def epilog(self) -> str:
        return "Examples:\n" + "\n".join(f"  {e}" for e in self.examples) + "\n"
