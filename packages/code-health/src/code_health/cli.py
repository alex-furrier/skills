"""Agent-friendly command-line interface for code-health."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from code_health import __version__
from code_health.core import analyze
from code_health.output import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    """Build the command surface."""
    parser = argparse.ArgumentParser(
        prog="code-health",
        description=(
            "Collect deterministic maintainability evidence without assigning a quality score."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    for command, help_text in (
        ("scan", "Analyze the current repository without a baseline."),
        ("diff", "Compare current findings with a Git baseline."),
    ):
        command_parser = subparsers.add_parser(
            command,
            help=help_text,
            description=help_text,
            epilog=(
                "Examples:\n"
                f"  code-health {command} . --format json\n"
                f"  code-health {command} /path/to/repo --format markdown"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        command_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Repository or nested path. Default: current directory.",
        )
        if command == "diff":
            command_parser.add_argument(
                "--base",
                default=None,
                help="Git revision or branch to compare. Default: origin HEAD, main, or master.",
            )
        command_parser.add_argument(
            "--churn-days",
            type=int,
            default=90,
            help="History window for per-file line churn. Default: 90.",
        )
        command_parser.add_argument(
            "--format",
            choices=("json", "markdown"),
            default="markdown",
            help="Output format. Default: markdown.",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run code-health."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command not in {"scan", "diff"}:
        parser.print_help(sys.stderr)
        return 2
    if args.churn_days <= 0:
        print("error: --churn-days must be greater than 0", file=sys.stderr)
        return 2
    try:
        report = analyze(
            Path(args.path),
            mode=args.command,
            base=getattr(args, "base", None),
            churn_days=args.churn_days,
        )
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(render_json(report))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
