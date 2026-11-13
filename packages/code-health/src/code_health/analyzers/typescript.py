"""ESLint 9 adapter with an isolated fixed syntax-only configuration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from code_health.models import Finding, ToolStatus
from code_health.process import run
from code_health.repository import IGNORED_PARTS, is_test_path

# Advisory hotspot thresholds: comparable complexity/params match Python; 100 lines
# matches Rust. Depth and callbacks are conservative navigation defaults.
ESLINT_RULES = {
    "complexity": ("cyclomatic-complexity", 10),
    "max-lines-per-function": ("function-lines", 100),
    "max-params": ("argument-count", 5),
    "max-depth": ("nesting-depth", 4),
    "max-nested-callbacks": ("nested-callbacks", 3),
}
NUMBER = re.compile(
    r"(?:of |is |has )?(\d+).*?(?:Maximum allowed is |max(?:imum)? is |limit is |>)\s*(\d+)", re.I
)
FUNCTION_NAME = re.compile(r"(?:Function|Method|Arrow function)\s+['\"]([^'\"]+)['\"]", re.I)
UNNAMED_ARROW_FUNCTION = re.compile(r"\bArrow function\b", re.I)


def _masked_source(source: str) -> str:
    """Mask strings and comments while preserving offsets for structural matching."""
    result = list(source)
    index = 0
    while index < len(source):
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            end = len(source) if end < 0 else end + 2
        elif source[index] in "'\"`":
            quote = source[index]
            end = index + 1
            while end < len(source):
                if source[end] == "\\":
                    end += 2
                elif source[end] == quote:
                    end += 1
                    break
                else:
                    end += 1
        else:
            index += 1
            continue
        for position in range(index, end):
            if result[position] != "\n":
                result[position] = " "
        index = end
    return "".join(result)


def _closing_paren(source: str, opening: int) -> int | None:
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _typescript_scopes(masked: str) -> list[tuple[int, int, str]]:
    """Return named class, object, and function brace ranges without a parser."""
    stack: list[tuple[int, str | None]] = []
    scopes: list[tuple[int, int, str]] = []
    for index, character in enumerate(masked):
        if character == "{":
            prefix = masked[max(0, index - 300) : index]
            name: str | None = None
            for pattern, kind in (
                (r"\bclass\s+([A-Za-z_$][\w$]*)[^{}]*$", "class"),
                (r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)[^{}=]*=\s*$", "object"),
                (r"\bfunction\s+([A-Za-z_$][\w$]*)[^{}]*$", "function"),
                (r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)[^{}=]*=.*=>\s*$", "function"),
            ):
                match = re.search(pattern, prefix, re.S)
                if match:
                    name = f"{kind}:{match.group(1)}"
                    break
            stack.append((index, name))
        elif character == "}" and stack:
            opening, name = stack.pop()
            if name:
                scopes.append((opening, index, name))
    return scopes


def _typescript_symbol(
    path: Path, line: int, name: str | None, column: int | None = None
) -> tuple[str | None, str | None]:
    """Resolve an ESLint diagnostic to a source-structural identity.

    The fixed ESLint JSON does not include AST node identities. This deliberately
    small lexical resolver only accepts a declaration on the reported line; an
    ambiguous or unsupported declaration is an evidence gap rather than a false
    baseline delta. Unnamed arrow diagnostics resolve only variable declarations
    or object properties assigned to an arrow, so an unrelated expression cannot
    acquire an identity.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, f"cannot read TypeScript source for identity: {error}"
    masked = _masked_source(source)
    starts = [0]
    starts.extend(index + 1 for index, character in enumerate(source) if character == "\n")
    if line < 1 or line > len(starts):
        return None, f"ESLint line {line} is outside TypeScript source"
    line_start = starts[line - 1]
    line_end = source.find("\n", line_start)
    line_end = len(source) if line_end < 0 else line_end
    if name is None:
        patterns = (
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?:[^=;{}()]*)?="
            r"\s*(?:async\s*)?(?:<[^(){}]*>\s*)?\(",
            r"\b([A-Za-z_$][\w$]*)\s*:\s*(?:async\s*)?(?:<[^(){}]*>\s*)?\(",
        )
    else:
        escaped = re.escape(name)
        patterns = (
            rf"\bfunction\s+({escaped})\b[^(){{}}]*\(",
            rf"\b(?:const|let|var)\s+({escaped})\s*=\s*(?:async\s*)?(?:<[^(){{}}]*>\s*)?\(",
            rf"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|readonly\s+)*({escaped})\s*(?:<[^(){{}}]*>)?\(",
            rf"\b({escaped})\s*:\s*(?:async\s*)?(?:<[^(){{}}]*>\s*)?\(",
        )
    declarations: list[tuple[int, int, str, str]] = []
    if name is None:
        single_parameter = re.compile(
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?:[^=;{}()]*)?="
            r"\s*(?:async\s+)?[A-Za-z_$][\w$]*\s*=>"
        )
        for match in single_parameter.finditer(masked):
            if not (line_start <= match.start(1) < line_end):
                continue
            arrow_position = masked.rfind("=>", match.start(), match.end())
            arrow_column = arrow_position - line_start + 1
            if column is not None and arrow_column != column:
                continue
            signature = re.sub(r"\s+", "", source[match.start() : arrow_position])
            declarations.append((match.start(1), arrow_position, signature, match.group(1)))
    for pattern in patterns:
        for match in re.finditer(pattern, masked, re.M):
            if not (line_start <= match.start(1) < line_end):
                continue
            opening = masked.find("(", match.start(1), match.end())
            closing = _closing_paren(masked, opening)
            if closing is None:
                continue
            if name is None:
                arrow = re.match(r"\s*=>", masked[closing + 1 :])
                if arrow is None:
                    continue
                arrow_position = closing + 1 + arrow.end() - len("=>")
                arrow_column = arrow_position - line_start + 1
                if column is not None and arrow_column != column:
                    continue
            signature = re.sub(r"\s+", "", source[match.start() : closing + 1])
            declarations.append((match.start(1), closing, signature, match.group(1)))
    declarations = list(dict.fromkeys(declarations))
    if len(declarations) != 1:
        descriptor = (
            f"named TypeScript declaration {name!r}" if name else "unnamed arrow declaration"
        )
        return None, f"cannot uniquely resolve {descriptor} on line {line}"
    position, _closing, signature, declaration_name = declarations[0]
    owners = [scope for scope in _typescript_scopes(masked) if scope[0] < position < scope[1]]
    owner = ".".join(item[2].split(":", 1)[1] for item in sorted(owners) if item[2])
    return (f"{owner}.{declaration_name}" if owner else declaration_name), signature


def _local_node_path(root: Path, target: Path, relative: str) -> Path | None:
    """Find a candidate-owned Node dependency from focused target through root."""
    start = target if target.is_dir() else target.parent
    for candidate in (start, *start.parents):
        try:
            candidate.relative_to(root)
        except ValueError:
            break
        path = candidate / relative
        if path.exists():
            return path
        if candidate == root:
            break
    return None


@dataclass(frozen=True)
class ESLintContext:
    executable: str
    parser: str
    version: str
    config: Path


def prepare_eslint(
    root: Path, temporary: Path, target: Path | None = None
) -> tuple[ESLintContext | None, ToolStatus]:
    resolution_target = target or root
    executable = _local_node_path(root, resolution_target, "node_modules/.bin/eslint")
    parser = _local_node_path(
        root, resolution_target, "node_modules/@typescript-eslint/parser/dist/index.js"
    )
    executable_text = str(executable) if executable else None
    command = (str(executable_text or "eslint"), "--version")
    if not executable_text:
        return None, ToolStatus("eslint", "unavailable", "ESLint 9 is not installed", command)
    if parser is None:
        return None, ToolStatus(
            "eslint",
            "unavailable",
            "@typescript-eslint/parser is not available in the candidate workspace",
            command,
        )
    version_result = run(command, cwd=root)
    version = version_result.stdout.strip()
    if version_result.returncode or not version.startswith("v9."):
        return None, ToolStatus(
            "eslint",
            "unavailable",
            f"ESLint 9 is required; found {version or 'an incompatible executable'}",
            command,
        )
    temporary.mkdir(parents=True, exist_ok=True)
    config = temporary / "eslint.config.mjs"
    rules = ",".join(
        f"'{rule}':['warn',{threshold}]" for rule, (_, threshold) in ESLINT_RULES.items()
    )
    config.write_text(
        "import parser from " + json.dumps(str(parser)) + ";\n"
        "export default [{files:['**/*.{ts,tsx,js,jsx,mts,cts}'],"
        f"languageOptions:{{parser}},rules:{{{rules}}}}}];\n"
    )
    return ESLintContext(executable_text, str(parser), version, config), ToolStatus(
        "eslint", "ok", f"ESLint {version} with fixed syntax-only config", command
    )


def run_eslint(
    target: Path, root: Path, context: ESLintContext | None = None
) -> tuple[list[Finding], ToolStatus]:
    if context is None:
        return [], ToolStatus("eslint", "unavailable", "ESLint preparation did not succeed")
    # With --config, ESLint resolves file globs from cwd, not the config directory.
    # Keep both snapshots rooted identically without writing to either source tree.
    target_argument = target.resolve().relative_to(root.resolve()).as_posix() or "."
    command = (
        context.executable,
        "--no-config-lookup",
        "--no-inline-config",
        "--config",
        str(context.config),
        "--format",
        "json",
        "--no-ignore",
        target_argument,
    )
    result = run(command, cwd=root)
    if result.returncode not in (0, 1):
        return [], ToolStatus(
            "eslint",
            "error",
            result.stderr.strip() or f"eslint exited {result.returncode}",
            command,
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return [], ToolStatus("eslint", "error", f"invalid ESLint JSON: {error}", command)
    # ESLint returns parser/configuration failures in its normal JSON payload and
    # may mix them with ordinary diagnostics. They invalidate fixed-rule evidence
    # for the whole snapshot, so detect them before any path or rule filtering.
    fatal_diagnostics: list[str] = []
    for file in payload:
        if int(file.get("fatalErrorCount", 0)):
            fatal_diagnostics.append(str(file.get("filePath", "unknown file")))
            continue
        for item in file.get("messages", []):
            if item.get("fatal") is True:
                detail = str(item.get("message", "fatal ESLint diagnostic")).strip()
                fatal_diagnostics.append(detail or "fatal ESLint diagnostic")
            elif item.get("ruleId") is None and "no matching configuration" in str(
                item.get("message", "")
            ):
                fatal_diagnostics.append(str(item["message"]))
    if fatal_diagnostics:
        return [], ToolStatus(
            "eslint",
            "error",
            "ESLint fatal/parser diagnostic or unmatched configuration prevents advisory evidence: "
            + fatal_diagnostics[0],
            command,
        )
    findings: list[Finding] = []
    for file in payload:
        path = Path(file.get("filePath", ""))
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        if is_test_path(Path(relative)) or any(
            part in IGNORED_PARTS for part in Path(relative).parts
        ):
            continue
        pending: list[tuple[dict, str, str, int, int, int | None, int, str | None, str | None]] = []
        for item in file.get("messages", []):
            rule = item.get("ruleId")
            if rule not in ESLINT_RULES:
                continue
            message = str(item.get("message", ""))
            match = NUMBER.search(message)
            metric, threshold = ESLINT_RULES[rule]
            value = int(match.group(1)) if match else None
            reported_threshold = int(match.group(2)) if match else threshold
            line = int(item.get("line", 0))
            column = int(item.get("column", 0))
            name = FUNCTION_NAME.search(message)
            symbol = signature = None
            if name:
                symbol, signature = _typescript_symbol(path, line, name.group(1))
                if symbol is None:
                    return [], ToolStatus(
                        "eslint",
                        "unavailable",
                        signature or "TypeScript identity evidence gap",
                        command,
                    )
            elif UNNAMED_ARROW_FUNCTION.search(message):
                # Resolve assigned arrows when ESLint reports their declaration.
                # Inline callbacks without a stable lexical name keep location identity.
                symbol, signature = _typescript_symbol(path, line, None, column)
                if symbol is None:
                    signature = None
            pending.append(
                (item, rule, metric, line, column, value, reported_threshold, symbol, signature)
            )
        duplicates: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
        for _item, rule, metric, _line, _column, _value, _threshold, symbol, signature in pending:
            if symbol is not None and signature is not None:
                duplicates.setdefault((rule, metric, symbol), []).append((symbol, signature))
        for key, entries in duplicates.items():
            signatures = [entry[1] for entry in entries]
            if len(entries) > 1 and len(set(signatures)) != len(signatures):
                return [], ToolStatus(
                    "eslint",
                    "unavailable",
                    f"cannot distinguish duplicate TypeScript declarations for {key[2]!r}",
                    command,
                )
        for (
            item,
            rule,
            metric,
            line,
            column,
            value,
            reported_threshold,
            symbol,
            signature,
        ) in pending:
            if symbol is None:
                symbol = f"line:{line}:column:{column}"
            else:
                # Always retain the declaration signature so a later same-owner
                # collision cannot change an existing finding's identity.
                symbol = f"{symbol}@signature:{signature}"
            findings.append(
                Finding(
                    "eslint",
                    rule,
                    metric,
                    relative,
                    line,
                    symbol,
                    value,
                    reported_threshold,
                    str(item.get("message", "")),
                    "non-test",
                )
            )
    return findings, ToolStatus(
        "eslint", "ok", f"{len(findings)} findings using ESLint {context.version}", command
    )
