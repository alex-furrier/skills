"""golangci-lint v2 adapter isolated from source and Go caches."""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from code_health.models import Finding, ToolStatus
from code_health.process import run
from code_health.repository import IGNORED_PARTS, is_test_path

# Advisory thresholds: complexity/arguments align with Python; 100 lines matches Rust;
# cognition, maintainability and 60 statements are conservative navigation defaults.
CONFIG = """version: "2"
linters:
  default: none
  enable: [gocyclo, gocognit, funlen, maintidx, revive]
  settings:
    gocyclo: {min-complexity: 10}
    gocognit: {min-complexity: 15}
    funlen: {lines: 100, statements: 60}
    maintidx: {under: 20}
    revive:
      rules:
        - name: argument-limit
          arguments: [5]
"""
FUNCTION_NAME = re.compile(r"(?:of func|Function '(?:name: )?)([A-Za-z_][A-Za-z0-9_]*)", re.I)
FUNCTION_DECLARATION = re.compile(
    r"^\s*func\s+(?:\((?P<receiver>[^)]*)\)\s+)?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.M,
)

RULES = {
    "gocyclo": "cyclomatic-complexity",
    "gocognit": "cognitive-complexity",
    "funlen": "function-lines",
    "maintidx": "maintainability-index",
    "revive": "argument-count",
}
# These intentionally recognize only the fixed linters' v2 diagnostic forms.  A
# value remains absent rather than guessing from arbitrary diagnostic prose.
VALUE_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "gocyclo": (re.compile(r"cyclomatic complexity\s+(\d+).*?>\s*(\d+)", re.I),),
    "gocognit": (re.compile(r"cognitive complexity\s+(\d+).*?>\s*(\d+)", re.I),),
    "funlen": (
        re.compile(r"Function '[^']+' has too many statements \((\d+)\s*>\s*(\d+)\)"),
        re.compile(r"Function '[^']+' is too long \((\d+)\s*>\s*(\d+)\)"),
    ),
    "maintidx": (re.compile(r"Maintainability Index:\s*(\d+)", re.I),),
    "revive": (
        re.compile(
            r"maximum number of arguments per function exceeded; max (\d+) but got (\d+)",
            re.I,
        ),
        re.compile(
            r"maximum number of arguments per function exceeded; got (\d+) but max (\d+)",
            re.I,
        ),
    ),
}


@dataclass(frozen=True)
class GoContext:
    executable: str
    version: str
    config: Path


def prepare_golangci(
    root: Path, temporary: Path, target: Path | None = None
) -> tuple[GoContext | None, ToolStatus]:
    exe = shutil.which("golangci-lint")
    command = (exe or "golangci-lint", "version")
    if not exe:
        return None, ToolStatus(
            "golangci-lint", "unavailable", "golangci-lint v2 is not installed", command
        )
    result = run(command, cwd=root)
    version = (result.stdout + result.stderr).strip()
    if result.returncode or "version 2." not in version:
        return None, ToolStatus(
            "golangci-lint",
            "unavailable",
            f"golangci-lint v2 is required; found {version or 'an incompatible executable'}",
            command,
        )
    config = temporary / "golangci.yml"
    config.write_text(CONFIG)
    return GoContext(exe, version, config), ToolStatus(
        "golangci-lint", "ok", f"{version} with fixed advisory config", command
    )


def _modules(target: Path, root: Path) -> list[Path]:
    """Return every repository module, or only a focused path's nearest owner."""
    target = target.parent if target.is_file() else target
    if target.resolve() == root.resolve():
        return sorted(
            {
                module.resolve()
                for go_mod in root.rglob("go.mod")
                if not any(part in IGNORED_PARTS for part in go_mod.relative_to(root).parts)
                for module in [go_mod.parent]
            },
            key=lambda module: module.as_posix(),
        )
    owner = target
    while owner != root.parent:
        if (owner / "go.mod").exists():
            return [owner]
        owner = owner.parent
    return sorted(
        {
            go_mod.parent.resolve()
            for go_mod in target.rglob("go.mod")
            if not any(part in IGNORED_PARTS for part in go_mod.relative_to(root).parts)
        },
        key=lambda module: module.as_posix(),
    )


def _strip_go_comments(source: str) -> tuple[str | None, str | None]:
    """Replace Go comments while preserving strings, lines, and malformed-input evidence."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(source):
        character = source[index]
        if quote == '"' and character == "\\":
            output.append(source[index : index + 2])
            index += 2
            continue
        if quote is not None:
            output.append(character)
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {'"', "`"}:
            quote = character
            output.append(character)
            index += 1
        elif source.startswith("//", index):
            newline = source.find("\n", index)
            if newline < 0:
                break
            output.append("\n")
            index = newline + 1
        elif source.startswith("/*", index):
            closing = source.find("*/", index + 2)
            if closing < 0:
                return None, "unterminated block comment"
            output.extend("\n" for char in source[index : closing + 2] if char == "\n")
            output.append(" ")
            index = closing + 2
        else:
            output.append(character)
            index += 1
    return "".join(output), None


def _unquote_go_string(value: str) -> str | None:
    """Unquote a Go interpreted string, including its non-JSON escape forms."""
    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
        return None
    output = bytearray()
    index = 1
    end = len(value) - 1
    simple_escapes = {"a": 7, "b": 8, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11}
    while index < end:
        character = value[index]
        if character in {"\n", "\r", '"'}:
            return None
        if character != "\\":
            output.extend(character.encode())
            index += 1
            continue
        index += 1
        if index == end:
            return None
        escape = value[index]
        if escape in simple_escapes:
            output.append(simple_escapes[escape])
            index += 1
        elif escape in {"\\", '"'}:
            output.extend(escape.encode())
            index += 1
        elif escape in "01234567":
            digits = value[index : index + 3]
            if len(digits) != 3 or any(digit not in "01234567" for digit in digits):
                return None
            output.append(int(digits, 8))
            index += 3
        elif escape in {"x", "u", "U"}:
            length = {"x": 2, "u": 4, "U": 8}[escape]
            digits = value[index + 1 : index + 1 + length]
            if len(digits) != length or any(
                digit not in "0123456789abcdefABCDEF" for digit in digits
            ):
                return None
            codepoint = int(digits, 16)
            if escape == "x":
                output.append(codepoint)
            elif codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                return None
            else:
                output.extend(chr(codepoint).encode())
            index += length + 1
        else:
            return None
    return os.fsdecode(bytes(output))


def _workspace_use_paths(root: Path) -> tuple[list[Path] | None, str | None]:
    """Return local go.work use paths, or an evidence gap explaining why not."""
    workspace = root / "go.work"
    if not workspace.exists():
        return [], None

    def use_path(line: str) -> str | None:
        line = line.strip()
        if line.startswith('"'):
            closing = line.rfind('"')
            if closing <= 0 or line[closing + 1 :].strip():
                return None
            path = _unquote_go_string(line[: closing + 1])
            return path or None
        if line.startswith("`"):
            closing = line.find("`", 1)
            if closing < 0 or line[closing + 1 :].strip():
                return None
            return line[1:closing] or None
        return line if line and not any(character.isspace() for character in line) else None

    try:
        source = workspace.read_text()
    except UnicodeDecodeError:
        return None, "go.work is not valid UTF-8"
    except OSError as error:
        detail = error.strerror or type(error).__name__
        return None, f"cannot read go.work: {detail}"
    uncommented, comment_gap = _strip_go_comments(source)
    if comment_gap:
        return None, comment_gap
    assert uncommented is not None
    paths: list[Path] = []
    in_use_block = False
    for raw_line in uncommented.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if in_use_block:
            if line == ")":
                in_use_block = False
                continue
            candidate = use_path(line)
            if candidate is None:
                return None, "malformed use block entry"
        elif match := re.fullmatch(r"use\s+(.+)", line):
            remainder = match.group(1).strip()
            if remainder == "(":
                in_use_block = True
                continue
            candidate = use_path(remainder)
            if candidate is None:
                return None, "malformed use directive"
        elif line.startswith("use"):
            return None, "malformed use directive"
        else:
            continue
        candidate_path = Path(candidate)
        if candidate_path.is_absolute():
            return (
                None,
                f"go.work references absolute path {candidate!r}; cannot relocate workspace safely",
            )
        path = (root / candidate_path).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            return (
                None,
                f"go.work references external path {candidate!r}; cannot copy workspace safely",
            )
        paths.append(path)
    if in_use_block:
        return None, "unterminated use block"
    return paths, None


def _workspace_environment(
    root: Path, copy_root: Path, module: Path
) -> tuple[str | None, str | None]:
    """Select a copied workspace only when it owns the module being analyzed."""
    paths, gap = _workspace_use_paths(root)
    if gap:
        return None, gap
    if not paths or module.resolve() not in paths:
        return "off", None
    return str((copy_root / "go.work").resolve()), None


def _metric_value_and_threshold(rule: str, message: str) -> tuple[str, int | None, int | None]:
    if rule == "maintidx":
        match = VALUE_PATTERNS[rule][0].search(message)
        return RULES[rule], int(match.group(1)) if match else None, 20 if match else None
    for index, pattern in enumerate(VALUE_PATTERNS[rule]):
        match = pattern.search(message)
        if not match:
            continue
        first, second = map(int, match.groups())
        if rule == "funlen":
            metric = "statement-count" if index == 0 else "function-lines"
            return metric, first, second
        if rule == "revive":
            return (RULES[rule], second, first) if index == 0 else (RULES[rule], first, second)
        return RULES[rule], first, second
    return RULES[rule], None, None


def _copy_repository(root: Path, copy_root: Path, ignored_names: set[str]) -> str | None:
    """Copy a repository without following symlinks outside its source boundary."""
    resolved_root = root.resolve()
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = [name for name in names if name not in ignored_names]
        for name in [*names, *(name for name in files if name not in ignored_names)]:
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            try:
                target = os.readlink(path)
                resolved = path.resolve(strict=True)
                resolved.relative_to(resolved_root)
            except (OSError, ValueError) as error:
                detail = getattr(error, "strerror", None) or str(error)
                return f"cannot safely copy symlink {path.relative_to(root)!s}: {detail}"
            if Path(target).is_absolute():
                return f"cannot safely copy absolute symlink {path.relative_to(root)!s}"
    try:
        shutil.copytree(
            root,
            copy_root,
            symlinks=True,
            ignore=lambda _directory, names: set(names) & ignored_names,
        )
    except OSError as error:
        detail = error.strerror or str(error)
        return f"cannot create disposable Go workspace copy: {detail}"
    return None


def _receiver_type_name(receiver: str) -> str | None:
    """Extract a receiver base type, ignoring local generic binder names."""
    tokens: list[str] = []
    start = 0
    bracket_depth = 0
    for index, character in enumerate(receiver):
        if character == "[":
            bracket_depth += 1
        elif character == "]":
            bracket_depth -= 1
            if bracket_depth < 0:
                return None
        elif character.isspace() and bracket_depth == 0:
            if token := receiver[start:index].strip():
                tokens.append(token)
            start = index + 1
    if bracket_depth:
        return None
    if token := receiver[start:].strip():
        tokens.append(token)
    if not tokens:
        return None
    receiver_type = re.sub(r"\s+", "", tokens[-1]).lstrip("*")
    return receiver_type.split("[", 1)[0] or None


def _function_name(source: Path, line: int, message: str) -> tuple[str | None, str | None]:
    """Return a stable function or receiver-qualified method name without a Go parser."""
    try:
        text = source.read_text()
    except (OSError, UnicodeDecodeError) as error:
        detail = getattr(error, "strerror", None) or str(error)
        return None, f"cannot read Go source {source.name}: {detail}"
    declarations = list(FUNCTION_DECLARATION.finditer(text))
    preceding = [match for match in declarations if text.count("\n", 0, match.start()) + 1 <= line]
    if preceding:
        declaration = preceding[-1]
        name = declaration.group("name")
        receiver = declaration.group("receiver")
        if receiver:
            receiver_type = _receiver_type_name(receiver)
            if receiver_type:
                return f"{receiver_type}.{name}", None
        return name, None
    if match := FUNCTION_NAME.search(message):
        return match.group(1), None
    return None, None


def _disambiguate_named_findings(findings: list[Finding]) -> list[Finding]:
    """Keep the first named identity stable and disambiguate later collisions."""
    seen: dict[tuple[str, str, str, str], int] = {}
    disambiguated: list[Finding] = []
    for finding in findings:
        if finding.symbol.startswith("line:"):
            disambiguated.append(finding)
            continue
        key = (finding.path, finding.rule, finding.metric, finding.symbol)
        occurrence = seen.get(key, 0)
        seen[key] = occurrence + 1
        if occurrence:
            finding = Finding(
                **{**finding.__dict__, "symbol": f"{finding.symbol}@line:{finding.line}"}
            )
        disambiguated.append(finding)
    return disambiguated


def _relative_issue_path(filename: str, copy_root: Path, prefix: Path) -> str | None:
    path = Path(filename)
    if path.is_absolute():
        try:
            relative = path.resolve().relative_to(copy_root.resolve())
        except ValueError:
            return None
        return relative.as_posix()
    if ".." in path.parts:
        return None
    # golangci-lint v2 may report a path relative to its disposable config
    # parent (for example ``go-analysis/source/file.go``), not its module cwd.
    # Normalize only that exact known workspace prefix before mapping it back to
    # the immutable source checkout.
    workspace_prefix = copy_root.parent.name, copy_root.name
    if path.parts[:2] == workspace_prefix:
        path = Path(*path.parts[2:])
    return (prefix / path).as_posix()


def run_golangci(
    target: Path, root: Path, context: GoContext | None = None
) -> tuple[list[Finding], ToolStatus]:
    if context is None:
        return [], ToolStatus(
            "golangci-lint", "unavailable", "golangci-lint preparation did not succeed"
        )
    modules = _modules(target, root)
    if not modules:
        return [], ToolStatus(
            "golangci-lint", "unavailable", "no Go module found for requested scope"
        )
    workspace_paths, workspace_gap = _workspace_use_paths(root)
    if workspace_gap:
        return [], ToolStatus("golangci-lint", "unavailable", workspace_gap)
    assert workspace_paths is not None
    workspace = context.config.parent / "go-analysis"
    copy_root = workspace / "source"
    shutil.rmtree(workspace, ignore_errors=True)
    # Preserve vendored Go modules so strict offline analysis remains useful.
    ignored_names = set(IGNORED_PARTS) - {"vendor"}
    try:
        state_relative = context.config.parent.resolve().relative_to(root.resolve())
        if state_relative.parts:
            ignored_names.add(state_relative.parts[0])
    except ValueError:
        pass
    copy_gap = _copy_repository(root, copy_root, ignored_names)
    if copy_gap:
        return [], ToolStatus("golangci-lint", "error", copy_gap)
    all_findings: list[Finding] = []
    commands: list[tuple[str, ...]] = []
    for module in modules:
        module_copy = copy_root / module.resolve().relative_to(root.resolve())
        output = workspace / f"findings-{len(commands)}.json"
        command = (
            context.executable,
            "run",
            "--config",
            str(context.config),
            "--modules-download-mode=readonly",
            "--tests=false",
            "--uniq-by-line=false",
            "--max-issues-per-linter=0",
            "--max-same-issues=0",
            "--output.json.path",
            str(output),
            "./...",
        )
        go_work, workspace_gap = _workspace_environment(root, copy_root, module)
        if workspace_gap:
            return all_findings, ToolStatus("golangci-lint", "unavailable", workspace_gap)
        assert go_work is not None
        result = run(
            command,
            cwd=module_copy,
            env={
                "GOCACHE": str(workspace / "go-cache"),
                "GOMODCACHE": str(workspace / "go-mod-cache"),
                "GOLANGCI_LINT_CACHE": str(workspace / "lint-cache"),
                "GOPROXY": "off",
                "GOSUMDB": "off",
                "GOTOOLCHAIN": "local",
                "GOWORK": go_work,
            },
            timeout_seconds=300,
        )
        commands.append(command)
        if result.returncode not in (0, 1):
            return all_findings, ToolStatus(
                "golangci-lint",
                "error",
                result.stderr.strip() or f"golangci-lint exited {result.returncode}",
                command,
            )
        if not output.exists():
            return all_findings, ToolStatus(
                "golangci-lint", "error", "golangci-lint v2 did not create JSON output", command
            )
        try:
            issues = json.loads(output.read_text()).get("Issues", [])
        except OSError as error:
            detail = error.strerror or str(error)
            return all_findings, ToolStatus(
                "golangci-lint",
                "error",
                f"cannot read golangci-lint JSON evidence: {detail}",
                command,
            )
        except json.JSONDecodeError as error:
            return all_findings, ToolStatus(
                "golangci-lint", "error", f"invalid golangci-lint JSON: {error}", command
            )
        typecheck_issues = [
            issue for issue in issues if str(issue.get("FromLinter", "")).casefold() == "typecheck"
        ]
        if typecheck_issues:
            detail = str(typecheck_issues[0].get("Text", "")).strip()
            return all_findings, ToolStatus(
                "golangci-lint",
                "error",
                "golangci-lint typecheck diagnostic prevents advisory evidence: "
                f"{detail or 'typecheck failed'}",
                command,
            )
        prefix = module.resolve().relative_to(root.resolve())
        for issue in issues:
            pos = issue.get("Pos", {})
            rel = _relative_issue_path(str(pos.get("Filename", "")), copy_root, prefix)
            if rel is None:
                continue
            try:
                (root / rel).resolve().relative_to(target.resolve())
            except ValueError:
                continue
            if is_test_path(Path(rel)) or any(x in IGNORED_PARTS for x in Path(rel).parts):
                continue
            rule = issue.get("FromLinter", "")
            if rule not in RULES:
                continue
            line, column = int(pos.get("Line", 0)), int(pos.get("Column", 0))
            message = str(issue.get("Text", ""))
            metric, value, threshold = _metric_value_and_threshold(rule, message)
            symbol, read_gap = _function_name(root / rel, line, message)
            if read_gap:
                return all_findings, ToolStatus("golangci-lint", "error", read_gap, command)
            all_findings.append(
                Finding(
                    "golangci-lint",
                    rule,
                    metric,
                    rel,
                    line,
                    symbol or f"line:{line}:{column}",
                    value,
                    threshold,
                    message,
                    "non-test",
                )
            )
    all_findings = _disambiguate_named_findings(all_findings)
    limitation = "unparsed diagnostics retain null value/threshold provenance"
    return all_findings, ToolStatus(
        "golangci-lint",
        "ok",
        (
            f"{len(all_findings)} findings across {len(modules)} module(s), "
            f"offline disposable repository workspace copies; {limitation}"
        ),
        commands[0],
    )
