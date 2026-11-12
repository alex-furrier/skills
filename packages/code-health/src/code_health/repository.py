"""Repository discovery, source sizing, baseline export, and churn evidence."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from code_health.process import run

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "_archive",
    "archive",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}


def discover_root(path: Path) -> Path:
    """Resolve the Git repository containing path."""
    candidate = path.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=candidate)
    if result.returncode != 0:
        detail = result.stderr.strip() or "not inside a Git repository"
        raise RuntimeError(f"cannot discover repository from {candidate}: {detail}")
    return Path(result.stdout.strip()).resolve()


def revision(root: Path, ref: str = "HEAD") -> str:
    """Resolve a revision to a full commit."""
    result = run(["git", "rev-parse", "--verify", ref], cwd=root)
    if result.returncode != 0:
        raise RuntimeError(f"cannot resolve Git revision {ref!r}: {result.stderr.strip()}")
    return result.stdout.strip()


def merge_base(root: Path, base: str) -> str:
    """Resolve the exact common ancestor used for branch comparison."""
    result = run(["git", "merge-base", base, "HEAD"], cwd=root)
    if result.returncode != 0:
        raise RuntimeError(f"cannot resolve merge base for {base!r}: {result.stderr.strip()}")
    return result.stdout.strip()


def repository_identity(root: Path) -> str:
    """Return a stable repository name across linked Git worktrees."""
    result = run(["git", "rev-parse", "--git-common-dir"], cwd=root)
    if result.returncode == 0 and result.stdout.strip():
        common_dir = Path(result.stdout.strip())
        if not common_dir.is_absolute():
            common_dir = root / common_dir
        resolved = common_dir.resolve()
        return resolved.parent.name if resolved.name == ".git" else resolved.name
    return root.name


def default_base(root: Path) -> str:
    """Select the repository's configured default branch."""
    symbolic = run(
        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        cwd=root,
    )
    if symbolic.returncode == 0 and symbolic.stdout.strip():
        return symbolic.stdout.strip()
    for candidate in ("main", "master"):
        if run(["git", "rev-parse", "--verify", candidate], cwd=root).returncode == 0:
            return candidate
    raise RuntimeError("cannot infer a base branch; pass --base explicitly")


def changed_paths(root: Path, base: str) -> set[str]:
    """Return files changed from the merge base through the working tree."""
    result = run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=root)
    if result.returncode != 0:
        raise RuntimeError(f"cannot diff against {base!r}: {result.stderr.strip()}")
    paths = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    paths.update(working_tree_paths(root))
    return paths


def working_tree_paths(root: Path) -> set[str]:
    """Return tracked and untracked working-tree paths."""
    paths: set[str] = set()
    working = run(["git", "diff", "--name-only", "HEAD"], cwd=root)
    if working.returncode == 0:
        paths.update(line.strip() for line in working.stdout.splitlines() if line.strip())
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root)
    if untracked.returncode == 0:
        paths.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return paths


def churn_by_path(root: Path, days: int) -> dict[str, int]:
    """Count added plus deleted lines per path over a bounded history window."""
    result = run(
        [
            "git",
            "log",
            f"--since={days} days ago",
            "--numstat",
            "--format=",
            "--",
        ],
        cwd=root,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cannot read Git churn: {result.stderr.strip()}")
    churn: dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        churn[parts[2]] = churn.get(parts[2], 0) + int(parts[0]) + int(parts[1])
    return churn


def _source_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix in {".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".go"}:
            yield path


def detect_languages(root: Path) -> list[str]:
    """Detect supported languages from active source files."""
    suffixes = {path.suffix for path in _source_files(root)}
    languages: list[str] = []
    if ".py" in suffixes:
        languages.append("python")
    if ".rs" in suffixes:
        languages.append("rust")
    if suffixes & {".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"}:
        languages.append("typescript")
    if ".go" in suffixes:
        languages.append("go")
    return languages


def is_test_path(path: Path) -> bool:
    """Return whether a repository-relative path is conventionally a test."""
    name = path.name
    return (
        any(part in {"tests", "test", "__tests__", "spec"} for part in path.parts)
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_test.go")
        or ".test." in name
        or ".spec." in name
    )


def size_metrics(root: Path) -> dict[str, int]:
    """Count active source and test lines with Rust inline-test awareness."""
    non_test_lines = 0
    test_lines = 0
    non_test_files = 0
    test_files = 0
    for path in _source_files(root):
        relative = path.relative_to(root)
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        if path.suffix == ".rs" and "#[cfg(test)]" in lines:
            marker = lines.index("#[cfg(test)]")
            non_test_lines += marker
            test_lines += len(lines) - marker
            non_test_files += 1
            test_files += 1
        elif is_test_path(relative):
            test_lines += len(lines)
            test_files += 1
        else:
            non_test_lines += len(lines)
            non_test_files += 1
    return {
        "non_test_lines": non_test_lines,
        "test_lines": test_lines,
        "non_test_files": non_test_files,
        "test_files": test_files,
    }


@contextmanager
def exported_revision(root: Path, ref: str) -> Iterator[Path]:
    """Materialize every tracked path from a Git revision without a worktree."""
    temp_dir = Path(tempfile.mkdtemp(prefix="code-health-base-"))
    destination = temp_dir / "repository"
    index_file = temp_dir / "index"
    environment = {"GIT_INDEX_FILE": str(index_file)}
    try:
        read_tree = run(["git", "read-tree", ref], cwd=root, env=environment)
        if read_tree.returncode != 0:
            detail = read_tree.stderr.strip() or f"git read-tree exited {read_tree.returncode}"
            raise RuntimeError(f"cannot read revision {ref!r}: {detail}")
        destination.mkdir()
        checkout = run(
            [
                "git",
                "checkout-index",
                "--all",
                f"--prefix={destination.as_posix()}/",
            ],
            cwd=root,
            env=environment,
        )
        if checkout.returncode != 0:
            detail = checkout.stderr.strip() or (f"git checkout-index exited {checkout.returncode}")
            raise RuntimeError(f"cannot materialize revision {ref!r}: {detail}")
        yield destination
    finally:
        shutil.rmtree(temp_dir)
