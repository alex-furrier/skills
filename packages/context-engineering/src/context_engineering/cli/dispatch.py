"""One dispatcher. Build the parser from the registry, run, render, exit."""

from __future__ import annotations

import argparse
import sys

from ..domain.result import AnalysisResult, LintResult
from .registry import Subcommand
from .render import emit_json, render_analysis, render_lint
from .subcommands import ALL


def _error(message: str, *, exit_code: int = 1) -> int:
    print(f"error: {message}", file=sys.stderr)
    return exit_code


def build_parser(subcommands: tuple[Subcommand, ...] = ALL) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-engineering",
        description=(
            "Read-only analyzer CLI for context-engineering. "
            "Inspect repository paths, contracts, history, and diffs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  context-engineering tier services/payments\n"
            "  context-engineering antipatterns modules/help-desk --json\n"
            "  context-engineering cross-cutting services/payments --discover\n"
            "  context-engineering skills ./skills --all\n"
            "  context-engineering contracts packages/api --json\n"
            "  context-engineering review . --base origin/main\n"
            "  context-engineering check . --base origin/main\n"
            "  context-engineering check . --all\n"
            "  context-engineering backfill . --cutoff HEAD --json\n"
        ),
    )
    sub = parser.add_subparsers(dest="subcommand", metavar="<subcommand>")

    for cmd in subcommands:
        sp = sub.add_parser(
            cmd.name,
            help=cmd.help,
            description=cmd.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=cmd.epilog(),
        )
        cmd.configure(sp)
        sp.add_argument("--json", action="store_true", help="emit JSON to stdout")
        sp.set_defaults(_handler=cmd)

    return parser


def _render(result, *, json_mode: bool) -> int:
    if json_mode:
        emit_json(result)
        if isinstance(result, (LintResult, AnalysisResult)):
            return 1 if result.has_errors else 0
        return 0
    if isinstance(result, LintResult):
        return render_lint(result)
    render_analysis(result)
    return 1 if result.has_errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "subcommand", None):
        parser.print_help()
        return 0

    cmd: Subcommand = args._handler
    result = cmd.run(args)

    if result is None:
        hint = cmd.examples[0] if cmd.examples else f"context-engineering {cmd.name} <path>"
        return _error(
            f"{cmd.name}: invalid target path. Try: {hint}",
            exit_code=2,
        )

    if not isinstance(result, (LintResult, AnalysisResult)):
        return _error(f"internal: {cmd.name} returned {type(result).__name__}")

    return _render(result, json_mode=args.json)
