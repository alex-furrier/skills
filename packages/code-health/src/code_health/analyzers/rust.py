"""Rust Clippy adapter."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from code_health.models import Finding, ToolStatus
from code_health.process import run
from code_health.repository import IGNORED_PARTS, is_test_path

CLIPPY_METRICS = {
    "clippy::cognitive_complexity": "cognitive-complexity",
    "clippy::too_many_lines": "function-lines",
    "clippy::too_many_arguments": "argument-count",
    "clippy::type_complexity": "type-complexity",
}
CARGO_COPY_IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "target",
}
VALUE_PATTERN = re.compile(r"\((\d+)\s*(?:>|/)\s*(\d+)\)")
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


def _rust_symbol(root: Path, path: str, line: int) -> str:
    try:
        lines = (root / path).read_text(errors="replace").splitlines()
    except OSError:
        return ""
    start = max(0, line - 1)
    function_name = ""
    for candidate in lines[start : start + 6]:
        match = RUST_FN_PATTERN.search(candidate)
        if match:
            function_name = match.group(1)
            break
    if not function_name:
        return ""
    depth = 0
    active_impls: list[tuple[int, str]] = []
    for candidate in lines[: start + 1]:
        impl_match = RUST_IMPL_PATTERN.search(candidate)
        if impl_match and "{" in candidate:
            active_impls.append((depth, impl_match.group(1)))
        depth += candidate.count("{") - candidate.count("}")
        active_impls = [item for item in active_impls if item[0] < depth]
    if active_impls:
        return f"{active_impls[-1][1]}::{function_name}"
    return function_name


def _cargo_manifest(target: Path, repository_root: Path) -> Path | None:
    candidate = target if target.is_dir() else target.parent
    while candidate == repository_root or repository_root in candidate.parents:
        manifest = candidate / "Cargo.toml"
        if manifest.exists():
            return manifest
        if candidate == repository_root:
            break
        candidate = candidate.parent
    manifests = [
        path
        for path in target.rglob("Cargo.toml")
        if not any(part in IGNORED_PARTS for part in path.relative_to(repository_root).parts)
    ]
    return manifests[0] if len(manifests) == 1 else None


def _cargo_selectors(manifest: Path) -> tuple[list[str], str] | None:
    metadata_command = (
        "cargo",
        "metadata",
        "--no-deps",
        "--format-version=1",
        "--manifest-path",
        str(manifest),
        "--locked",
    )
    result = run(metadata_command, cwd=manifest.parent)
    if result.returncode != 0:
        return None
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    packages = metadata.get("packages", [])
    kinds = {
        kind
        for package in packages
        for target in package.get("targets", [])
        for kind in target.get("kind", [])
    }
    workspace_members = set(metadata.get("workspace_members", []))
    selectors: list[str] = []
    labels: list[str] = []
    if len(workspace_members) > 1:
        selectors.append("--workspace")
        labels.append("workspace")
    if kinds & {"lib", "rlib", "dylib", "cdylib", "staticlib", "proc-macro"}:
        selectors.append("--lib")
        labels.append("library")
    if "bin" in kinds:
        selectors.append("--bins")
        labels.append("binary")
    return (selectors, " and ".join(labels)) if selectors else None


def run_clippy(target: Path, repository_root: Path) -> tuple[list[Finding], ToolStatus]:
    """Run selected Clippy maintainability lints for Rust library and binary targets."""
    if shutil.which("cargo") is None:
        return [], ToolStatus("clippy", "unavailable", "cargo is not installed")
    source_manifest = _cargo_manifest(target, repository_root)
    if source_manifest is None:
        return [], ToolStatus(
            "clippy",
            "unavailable",
            "no unambiguous Cargo manifest found for target",
        )
    try:
        with tempfile.TemporaryDirectory(prefix="code-health-cargo-") as temporary:
            temporary_root = Path(temporary)
            analysis_root = temporary_root / "repository"
            shutil.copytree(
                repository_root,
                analysis_root,
                ignore_dangling_symlinks=True,
                ignore=lambda _directory, names: set(names) & CARGO_COPY_IGNORED_PARTS,
            )
            manifest = analysis_root / source_manifest.relative_to(repository_root)
            selection = _cargo_selectors(manifest)
            if selection is None:
                return [], ToolStatus(
                    "clippy",
                    "error",
                    f"cannot resolve Cargo library/binary targets from {source_manifest}",
                )
            selectors, target_label = selection
            command = (
                "env",
                "CARGO_TARGET_DIR=<temporary>",
                "CARGO_CACHE_RUSTC_INFO=0",
                "cargo",
                "clippy",
                "--manifest-path",
                (f"<disposable-copy>/{source_manifest.relative_to(repository_root).as_posix()}"),
                *selectors,
                "--message-format=json",
                "--locked",
                "--",
                "-W",
                "clippy::cognitive_complexity",
                "-W",
                "clippy::too_many_lines",
                "-W",
                "clippy::too_many_arguments",
                "-W",
                "clippy::type_complexity",
            )
            execution_command = (
                "cargo",
                "clippy",
                "--manifest-path",
                str(manifest),
                *command[7:],
            )
            result = run(
                execution_command,
                cwd=manifest.parent,
                timeout_seconds=300,
                env={
                    "CARGO_TARGET_DIR": str(temporary_root / "target"),
                    "CARGO_CACHE_RUSTC_INFO": "0",
                },
            )
    except RuntimeError as error:
        return [], ToolStatus("clippy", "error", str(error))
    except OSError as error:
        return [], ToolStatus("clippy", "error", f"cannot isolate Cargo sources: {error}")
    findings: list[Finding] = []
    for line in result.stdout.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("reason") != "compiler-message":
            continue
        message = payload.get("message") or {}
        code = (message.get("code") or {}).get("code")
        if code not in CLIPPY_METRICS:
            continue
        spans = message.get("spans") or []
        primary = next((span for span in spans if span.get("is_primary")), None)
        if primary is None:
            continue
        path = _relative_path(
            str(primary.get("file_name", "")),
            analysis_root,
            manifest.parent,
        )
        if not _active(path) or _scope(path) == "test":
            continue
        try:
            (repository_root / path).resolve().relative_to(target.resolve())
        except ValueError:
            continue
        text = str(message.get("message", ""))
        value, threshold = _value_and_threshold(text)
        line_start = int(primary.get("line_start", 0))
        findings.append(
            Finding(
                tool="clippy",
                rule=code,
                metric=CLIPPY_METRICS[code],
                path=path,
                line=line_start,
                symbol=_rust_symbol(repository_root, path, line_start),
                value=value,
                threshold=threshold,
                message=text,
                scope="non-test",
            )
        )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"cargo clippy exited {result.returncode}"
        return findings, ToolStatus("clippy", "error", detail, command)
    return findings, ToolStatus(
        "clippy",
        "ok",
        (
            f"{len(findings)} findings across {target_label} targets; "
            "executed in a disposable source copy with isolated Cargo output"
        ),
        command,
    )
