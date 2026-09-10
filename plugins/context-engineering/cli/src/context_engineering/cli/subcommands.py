"""The subcommands — each a tiny configure() + run() pair.

This is the whole CLI surface. Adding a subcommand means adding one entry
here, not editing a 350-line dispatcher.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..analysis import backfill as backfill_mod
from ..analysis import context_check as context_check_mod
from ..analysis import context_review as context_review_mod
from ..analysis import sessions as sessions_mod
from ..analysis import staleness as staleness_mod
from ..analysis import tier as tier_mod
from ..analysis.cross_cutting import discover as cc_discover
from ..analysis.cross_cutting import pair as cc_pair
from ..checks import contracts as contracts_mod
from ..checks import depth as depth_mod
from ..checks import frontmatter as frontmatter_mod
from ..checks import references as references_mod
from ..checks import skill_structure as skill_mod
from ..checks.antipatterns import lint as antipatterns_lint
from ..infra.git import git_root
from .registry import Subcommand


def _add_target(parser: argparse.ArgumentParser, help_text: str) -> None:
    parser.add_argument("path", help=help_text)


def _resolve(path_str: str) -> Path | None:
    p = Path(path_str).expanduser().resolve()
    return p if p.exists() else None


def _resolve_git_scope(path_str: str) -> Path | None:
    path = Path(path_str).expanduser().resolve()
    if path.exists() and not path.is_dir():
        return None
    return path if git_root(path) is not None else None


# ---------------------------------------------------------------------------
# tier
# ---------------------------------------------------------------------------


def _configure_tier(p: argparse.ArgumentParser) -> None:
    _add_target(p, "module path to classify (e.g., services/payments)")
    p.add_argument(
        "--lookback-days",
        type=int,
        default=90,
        metavar="DAYS",
        help="window of recent commits to consider (default: %(default)s)",
    )


def _run_tier(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return tier_mod.analyze(target, lookback_days=args.lookback_days)


TIER = Subcommand(
    name="tier",
    help="classify a module by unique author count (opinion-density tier)",
    description="Classify a module's opinion-density tier from recent unique authors.",
    examples=(
        "context-engineering tier services/payments",
        "context-engineering tier packages/api --lookback-days 180 --json",
    ),
    configure=_configure_tier,
    run=_run_tier,
)


# ---------------------------------------------------------------------------
# antipatterns
# ---------------------------------------------------------------------------


def _configure_antipatterns(p: argparse.ArgumentParser) -> None:
    _add_target(p, "directory to scan (e.g., services/payments)")
    p.add_argument(
        "--modified",
        action="store_true",
        help="only scan files in git status (also checks watermark staleness)",
    )


def _run_antipatterns(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None or not target.is_dir():
        # Must be a directory — the runner discovers files under `root`.
        # Returning None here routes through dispatch's "invalid target path"
        # diagnostic, matching the old script's explicit sys.exit(1) guard.
        return None
    return antipatterns_lint(target, modified_only=args.modified)


ANTIPATTERNS = Subcommand(
    name="antipatterns",
    help="scan AGENTS.md / docs/ files for content antipatterns",
    description="Scan for volatile content, watermark drift, size limits, splitting candidates.",
    examples=(
        "context-engineering antipatterns services/payments",
        "context-engineering antipatterns modules/help-desk --modified --json",
    ),
    configure=_configure_antipatterns,
    run=_run_antipatterns,
)


# ---------------------------------------------------------------------------
# depth
# ---------------------------------------------------------------------------


def _configure_depth(p: argparse.ArgumentParser) -> None:
    _add_target(p, "AGENTS.md file or directory")


def _run_depth(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return depth_mod.lint(target)


DEPTH = Subcommand(
    name="depth",
    help="compute AGENTS.md depth + P3 stringency warnings",
    description="Compute depth and run depth-appropriate stringency checks.",
    examples=(
        "context-engineering depth services/payments/AGENTS.md",
        "context-engineering depth packages/api --json",
    ),
    configure=_configure_depth,
    run=_run_depth,
)


# ---------------------------------------------------------------------------
# staleness
# ---------------------------------------------------------------------------


def _configure_staleness(p: argparse.ArgumentParser) -> None:
    _add_target(p, "path to AGENTS.md")


def _run_staleness(args: argparse.Namespace):
    # Staleness accepts non-existent AGENTS.md paths — returns "full-rebuild"
    # as the recommendation, which is the correct answer for "should this
    # not-yet-created AGENTS.md be generated?". Don't gate on path existence.
    return staleness_mod.analyze(Path(args.path).expanduser().resolve())


STALENESS = Subcommand(
    name="staleness",
    help="check staleness of an AGENTS.md relative to git activity",
    description="Categorize changes since last update and emit an update recommendation.",
    examples=(
        "context-engineering staleness services/payments/AGENTS.md",
        "context-engineering staleness modules/help-desk/AGENTS.md --json",
    ),
    configure=_configure_staleness,
    run=_run_staleness,
)


# ---------------------------------------------------------------------------
# sessions
# ---------------------------------------------------------------------------


def _configure_sessions(p: argparse.ArgumentParser) -> None:
    _add_target(p, "path to a project directory")
    p.add_argument("--max", type=int, default=20, metavar="N", help="maximum artifacts to return")
    p.add_argument("--sessions-dir", help="optional directory of exported JSONL session artifacts; absent is an explicit portable fallback")


def _run_sessions(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return sessions_mod.analyze(str(target), max_results=args.max, sessions_dir=args.sessions_dir)


SESSIONS = Subcommand(
    name="sessions",
    help="discover Claude Code sessions relevant to a path",
    description="Rank explicitly configured exported JSONL artifacts by mentions of the target.",
    examples=(
        "context-engineering sessions /abs/path/to/services/payments --max 5",
        "context-engineering sessions /abs/path/to/modules/help-desk --json",
    ),
    configure=_configure_sessions,
    run=_run_sessions,
)


# ---------------------------------------------------------------------------
# cross-cutting
# ---------------------------------------------------------------------------


def _configure_cross_cutting(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "paths",
        nargs="+",
        help="one path (with --discover) or several for pair mode",
    )
    p.add_argument(
        "--discover",
        action="store_true",
        help="discover mode: auto-find modules coupled to a single target "
        "(requires exactly one path)",
    )
    p.add_argument(
        "--lookback-days",
        type=int,
        default=90,
        metavar="DAYS",
        help="git history window for co-change/author signals (default: %(default)s)",
    )
    p.add_argument(
        "--min-edge",
        type=int,
        default=3,
        metavar="N",
        help="drop edges weaker than N from the output (default: %(default)s)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="cap discover results at top N per signal (default: %(default)s)",
    )
    p.add_argument(
        "--signals",
        default="imports,co-change,authors",
        metavar="CSV",
        help=("comma-separated subset of `imports`, `co-change`, `authors` (default: %(default)s)"),
    )


def _run_cross_cutting(args: argparse.Namespace):
    resolved = [_resolve(p) for p in args.paths]
    if any(p is None for p in resolved):
        return None
    paths = [p for p in resolved if p is not None]
    signals = frozenset(s.strip() for s in args.signals.split(","))
    if args.discover:
        if len(paths) != 1:
            return None
        return cc_discover(
            target_path=paths[0],
            lookback_days=args.lookback_days,
            min_edge=args.min_edge,
            top_n=args.top,
            signals=signals,
        )
    return cc_pair(
        module_paths=paths,
        lookback_days=args.lookback_days,
        min_edge=args.min_edge,
        signals=signals,
    )


CROSS_CUTTING = Subcommand(
    name="cross-cutting",
    help="imports/co-change/author-overlap between modules",
    description="Surface cross-cutting concerns via three signals.",
    examples=(
        "context-engineering cross-cutting services/payments --discover",
        "context-engineering cross-cutting packages/api services/payments --min-edge 5 --json",
    ),
    configure=_configure_cross_cutting,
    run=_run_cross_cutting,
)


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------


def _configure_frontmatter(p: argparse.ArgumentParser) -> None:
    _add_target(p, "directory containing docs/*.md files")


def _run_frontmatter(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return frontmatter_mod.lint(target)


FRONTMATTER = Subcommand(
    name="frontmatter",
    help="validate docs YAML frontmatter when the target establishes that convention",
    description=("Validate id/title/description/index[] consistency without imposing frontmatter."),
    examples=(
        "context-engineering frontmatter services/payments",
        "context-engineering frontmatter managed configuration/modules/context-engineering --json",
    ),
    configure=_configure_frontmatter,
    run=_run_frontmatter,
)


# ---------------------------------------------------------------------------
# references
# ---------------------------------------------------------------------------


def _configure_references(p: argparse.ArgumentParser) -> None:
    _add_target(p, "directory to scan")


def _run_references(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return references_mod.lint(target)


REFERENCES = Subcommand(
    name="references",
    help="verify backtick paths, CLAUDE.md symlinks, docs indexes",
    description="Check that references resolve and CLAUDE.md files are valid symlinks.",
    examples=(
        "context-engineering references services/payments",
        "context-engineering references modules/help-desk --json",
    ),
    configure=_configure_references,
    run=_run_references,
)


# ---------------------------------------------------------------------------
# skills
# ---------------------------------------------------------------------------


def _configure_skills(p: argparse.ArgumentParser) -> None:
    _add_target(p, "skill directory (or parent with --all)")
    p.add_argument(
        "--all",
        action="store_true",
        dest="recurse",
        help="validate every skill directory under <path>",
    )


def _run_skills(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None:
        return None
    return skill_mod.lint(target, recurse=args.recurse)


SKILLS = Subcommand(
    name="skills",
    help="validate skill directory structure",
    description="Validate one skill directory (or --all skills under a parent).",
    examples=(
        "context-engineering skills ./skills/context-agents-md",
        "context-engineering skills ./skills --all --json",
    ),
    configure=_configure_skills,
    run=_run_skills,
)


# ---------------------------------------------------------------------------
# contracts / review / backfill
# ---------------------------------------------------------------------------


def _configure_contracts(p: argparse.ArgumentParser) -> None:
    _add_target(p, "repository or module root containing optional SPEC.md and ADRs")
    p.add_argument("--require-spec", action="store_true", help="error when SPEC.md is absent")
    p.add_argument(
        "--require-adrs",
        action="store_true",
        help="error when no valid ADR record exists",
    )


def _run_contracts(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None or not target.is_dir():
        return None
    return contracts_mod.analyze(
        target,
        require_spec=args.require_spec,
        require_adrs=args.require_adrs,
    )


CONTRACTS = Subcommand(
    name="contracts",
    help="discover and validate optional SPEC.md and ADR contracts",
    description="Discover existing contract conventions and validate deterministic SPEC/ADR rules.",
    examples=(
        "context-engineering contracts .",
        "context-engineering contracts packages/api --require-spec --json",
    ),
    configure=_configure_contracts,
    run=_run_contracts,
)


def _configure_review(p: argparse.ArgumentParser) -> None:
    _add_target(p, "repository or module root to scope the diff")
    p.add_argument(
        "--base",
        required=True,
        metavar="REF",
        help="base Git ref for the three-dot diff",
    )
    p.add_argument(
        "--head",
        default="HEAD",
        metavar="REF",
        help="head Git ref (default: %(default)s)",
    )


def _run_review(args: argparse.Namespace):
    target = _resolve_git_scope(args.path)
    if target is None:
        return None
    return context_review_mod.analyze(target, base=args.base, head=args.head)


REVIEW = Subcommand(
    name="review",
    help="inspect a diff for advisory context update routes",
    description=(
        "Preserve raw Git evidence and suggest advisory context owners without writing files."
    ),
    examples=(
        "context-engineering review . --base origin/main",
        "context-engineering review packages/api --base v1.2.0 --head HEAD --json",
    ),
    configure=_configure_review,
    run=_run_review,
)


def _configure_check(p: argparse.ArgumentParser) -> None:
    _add_target(p, "repository or module root to validate at the exact head tree")
    p.add_argument(
        "--base",
        metavar="REF",
        help="base Git ref for changed-owner validation; omit with --all",
    )
    p.add_argument(
        "--head", default="HEAD", metavar="REF", help="head Git ref (default: %(default)s)"
    )
    p.add_argument(
        "--all",
        dest="all_context",
        action="store_true",
        help="validate every discovered context owner, not only affected owners",
    )


def _run_check(args: argparse.Namespace):
    target = _resolve_git_scope(args.path)
    if target is None:
        return None
    all_context = args.all_context or args.base is None
    return context_check_mod.analyze(
        target,
        base=args.base or args.head,
        head=args.head,
        all_context=all_context,
    )


CHECK = Subcommand(
    name="check",
    help="run the composed deterministic PR-time context check",
    description=(
        "Validate affected context owners at the exact head tree and report semantic routes "
        "separately as advisory evidence."
    ),
    examples=(
        "context-engineering check . --base origin/main",
        "context-engineering check . --all --json",
    ),
    configure=_configure_check,
    run=_run_check,
)


def _configure_backfill(p: argparse.ArgumentParser) -> None:
    _add_target(p, "repository or module root whose local Git history should be extracted")
    p.add_argument(
        "--publish-safe",
        action="store_true",
        help="omit raw historical subjects and paths from the rendered response",
    )
    p.add_argument(
        "--cutoff",
        default="HEAD",
        metavar="REF",
        help="latest Git ref visible to reconstruction (default: %(default)s)",
    )
    p.add_argument(
        "--quick",
        action="store_true",
        help=(
            "use a bounded current-state reconstruction instead of the default "
            "complete-picture genesis-through-cutoff history"
        ),
    )
    p.add_argument(
        "--max-commits",
        type=int,
        default=None,
        metavar="N",
        help=(
            "maximum local commits in --quick mode (default with --quick: 100); "
            "rejected without --quick"
        ),
    )


def _run_backfill(args: argparse.Namespace):
    target = _resolve(args.path)
    if target is None or not target.is_dir():
        return None
    return backfill_mod.analyze(
        target,
        cutoff=args.cutoff,
        max_commits=args.max_commits,
        quick=args.quick,
        publish_safe=args.publish_safe,
    )


BACKFILL = Subcommand(
    name="backfill",
    help="extract provenance-preserving local Git history for contract backfill",
    description=(
        "Return deterministic read-only historical evidence for agent-owned synthesis: "
        "complete-picture by default, or bounded current-state reconstruction with --quick. "
        "The CLI never writes files and does not author claims, SPEC content, ADR decisions, "
        "or documentation."
    ),
    examples=(
        "context-engineering backfill . --cutoff HEAD",
        "context-engineering backfill . --cutoff HEAD --json",
        "context-engineering backfill packages/api --cutoff v1.2.0 --quick --max-commits 50 --json",
    ),
    configure=_configure_backfill,
    run=_run_backfill,
)


ALL: tuple[Subcommand, ...] = (
    TIER,
    ANTIPATTERNS,
    DEPTH,
    STALENESS,
    SESSIONS,
    CROSS_CUTTING,
    FRONTMATTER,
    REFERENCES,
    SKILLS,
    CONTRACTS,
    REVIEW,
    CHECK,
    BACKFILL,
)
