"""Python Ruff adapter."""

from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path

from code_health.models import Finding, ToolStatus
from code_health.process import run
from code_health.repository import IGNORED_PARTS, is_test_path

RUFF_RULES = ("C901", "PLR0911", "PLR0912", "PLR0913", "PLR0915")
RUFF_METRICS = {
    "C901": "cyclomatic-complexity",
    "PLR0911": "return-count",
    "PLR0912": "branch-count",
    "PLR0913": "argument-count",
    "PLR0915": "statement-count",
}
VALUE_PATTERN = re.compile(r"\((\d+)\s*(?:>|/)\s*(\d+)\)")
SYMBOL_PATTERN = re.compile(r"`([^`]+)`")
RUST_FN_PATTERN = re.compile(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)")
RUST_IMPL_PATTERN = re.compile(
    r"\bimpl(?:<[^>]*>)?\s+(?:[^\s{]+\s+for\s+)?([A-Za-z_][A-Za-z0-9_:<>]*)"
)


def _relative_path(path_text: str, root: Path, source_root: Path | None = None) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        path = (source_root or root) / path
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _scope(path: str) -> str:
    return "test" if is_test_path(Path(path)) else "non-test"


def _active(path: str) -> bool:
    return not any(part in IGNORED_PARTS for part in Path(path).parts)


def _value_and_threshold(message: str) -> tuple[int | None, int | None]:
    match = VALUE_PATTERN.search(message)
    if match is None:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _python_symbol(root: Path, path: str, line: int) -> str:
    """Return the smallest Python function containing a finding line."""
    try:
        tree = ast.parse((root / path).read_text(errors="replace"))
    except (OSError, SyntaxError):
        return ""
    candidates: list[tuple[int, str]] = []

    def visit(node: ast.AST, owners: tuple[str, ...] = ()) -> None:
        child_owners = owners
        if isinstance(node, ast.ClassDef):
            child_owners = (*owners, node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            qualified = ".".join((*owners, node.name))
            if node.lineno <= line <= end_line:
                candidates.append((end_line - node.lineno, qualified))
            child_owners = (*owners, node.name)
        for child in ast.iter_child_nodes(node):
            visit(child, child_owners)

    visit(tree)
    return min(candidates)[1] if candidates else ""


def run_ruff(target: Path, repository_root: Path) -> tuple[list[Finding], ToolStatus]:
    """Run Ruff's selected maintainability rules."""
    # Exports contain only tracked paths. Match that boundary in live checkouts,
    # regardless of Git ignore rules; never feed untracked output to Ruff.
    if (repository_root / ".git").exists():
        tracked = run(["git", "ls-files", "--cached", "-z"], cwd=repository_root)
        if tracked.returncode != 0:
            return [], ToolStatus("ruff", "error", tracked.stderr.strip())
        candidates = (repository_root / name for name in tracked.stdout.split("\0") if name)
    else:
        candidates = target.rglob("*.py") if target.is_dir() else iter([target])
    sources = sorted(
        {
            path
            for path in candidates
            if path.suffix == ".py"
            and path.is_file()
            and (path == target or target in path.parents)
            and _active(path.relative_to(repository_root).as_posix())
        }
    )
    command = (
        "ruff",
        "check",
        *(str(path) for path in sources),
        "--no-respect-gitignore",
        "--force-exclude",
        "--select",
        ",".join(RUFF_RULES),
        "--output-format",
        "json",
        "--exit-zero",
        "--no-cache",
    )
    if shutil.which("ruff") is None:
        return [], ToolStatus("ruff", "unavailable", "ruff is not installed", command)
    if not sources:
        return [], ToolStatus("ruff", "ok", "0 active tracked Python files", command)
    try:
        result = run(command, cwd=repository_root)
    except RuntimeError as error:
        return [], ToolStatus("ruff", "error", str(error), command)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"ruff exited {result.returncode}"
        return [], ToolStatus("ruff", "error", detail, command)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return [], ToolStatus("ruff", "error", f"invalid Ruff JSON: {error}", command)
    for item in payload:
        if item.get("code") in {"invalid-syntax", "E999", "syntax-error"}:
            return [], ToolStatus(
                "ruff",
                "error",
                "Ruff syntax diagnostic prevents advisory evidence: "
                + str(item.get("message", "invalid Python syntax")),
                command,
            )
    findings: list[Finding] = []
    for item in payload:
        code = item.get("code")
        if code not in RUFF_METRICS:
            continue
        path = _relative_path(str(item.get("filename", "")), repository_root)
        if not _active(path) or _scope(path) == "test":
            continue
        message = str(item.get("message", ""))
        value, threshold = _value_and_threshold(message)
        symbol_match = SYMBOL_PATTERN.search(message)
        location = item.get("location") or {}
        line = int(location.get("row", 0))
        qualified_symbol = _python_symbol(repository_root, path, line)
        findings.append(
            Finding(
                tool="ruff",
                rule=code,
                metric=RUFF_METRICS[code],
                path=path,
                line=line,
                symbol=qualified_symbol or (symbol_match.group(1) if symbol_match else ""),
                value=value,
                threshold=threshold,
                message=message,
                scope="non-test",
            )
        )
    return findings, ToolStatus("ruff", "ok", f"{len(findings)} findings", command)
