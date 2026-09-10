"""Verify that paths referenced in AGENTS.md / docs/*.md files resolve.

`is_likely_path` is a series of small named predicates — each rules out a
specific kind of non-path that happens to appear in backticks. Adding a new
exclusion means adding a one-liner, not extending a 15-branch function.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ..analysis.context_layout import RepositoryContextLayout, discover
from ..domain.finding import Finding, Severity
from ..domain.result import LintResult
from ..infra.filesystem import EXCLUDED_DIRS, read_text_safe

# ---------------------------------------------------------------------------
# Path-likeness heuristic — factored into named predicates so adding
# exclusions doesn't mean touching a 30-branch function.
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"^(https?|git\+https?|gs|gcr\.io|docker\.io)[:/]")
_ENV_OR_FLAG_RE = re.compile(r"^(--|\$|[A-Z_]+=|@|#|\*|>)")
_KEYBINDING_RE = re.compile(r"^(Alt|Ctrl|Shift|Meta|Cmd|Super)\+")
_VIM_KEY_RE = re.compile(r"^<(leader|prefix|space|cr|esc|tab|bs|del|up|down|left|right)")
_DOMAIN_RE = re.compile(r"^\w+\.\w+\.\w+/")
_CONTAINER_TAG_RE = re.compile(r":\w[\w.-]*$")
_DOTTED_PROP_RE = re.compile(r"\w+(\.\w+)+")
# Deliberately narrow: only match bare org/repo when no file extension would
# distinguish it. Two-segment repo paths like `services/payments` match the
# filesystem-resolution fallback, so we accept them as path candidates and let
# the resolver decide. Matching `foo/bar` as "github repo" caused broken
# references to pass silently.
_TOOL_OUTPUT_DIR_RE = re.compile(r"^\.[a-zA-Z][\w-]*(/|$)")
_UPPERCASE_PROPERTY_RE = re.compile(r"\.[a-z]*[A-Z]\w*$")  # .sourceDir, .chezmoi
_DOTTED_METHOD_NAMES = {".parent", ".name", ".stem", ".suffix", ".resolve"}


def _looks_like_prose(text: str) -> bool:
    """Strings that can't possibly be file paths."""
    return (
        not text
        or len(text) < 3
        or " " in text
        or any(c in text for c in "()=;{}<>\"'")
        or "{{" in text
        or "*" in text
        or "?" in text
    )


def _is_homebrew_tap(text: str) -> bool:
    return text.startswith(("brew ", "tap ", "homebrew/"))


def _is_home_or_absolute(text: str) -> bool:
    return text.startswith(("/", "~/", "~"))


def _is_protocol_uri(text: str) -> bool:
    return bool(_URL_RE.match(text)) or text.startswith(
        ("collection://", "discussion://", "notion://")
    )


def _is_flag_or_cli(text: str) -> bool:
    return bool(_ENV_OR_FLAG_RE.match(text))


def _is_shortcut(text: str) -> bool:
    return bool(_KEYBINDING_RE.match(text) or _VIM_KEY_RE.match(text))


def _is_domain_path(text: str) -> bool:
    return bool(_DOMAIN_RE.match(text))


def _is_tool_output_dir(text: str) -> bool:
    return bool(_TOOL_OUTPUT_DIR_RE.match(text))


def _is_bare_extension(text: str) -> bool:
    return "/" not in text and text.startswith(".") and bool(re.fullmatch(r"\.\w+", text))


def _is_dotted_config_key(text: str) -> bool:
    return "/" not in text and bool(_DOTTED_PROP_RE.fullmatch(text))


def _is_uppercase_property(text: str) -> bool:
    return "/" not in text and bool(_UPPERCASE_PROPERTY_RE.search(text))


def _is_dotted_method(text: str) -> bool:
    return "/" not in text and any(text.endswith(m) for m in _DOTTED_METHOD_NAMES)


def _is_container_image(text: str) -> bool:
    return ":" in text and bool(_CONTAINER_TAG_RE.search(text))


def _looks_pathish(text: str) -> bool:
    has_slash = "/" in text
    has_extension = bool(re.search(r"\.\w{1,10}$", text))
    return has_slash or has_extension


_NON_PATH_PREDICATES = (
    _is_homebrew_tap,
    _is_home_or_absolute,
    _is_protocol_uri,
    _is_flag_or_cli,
    _is_shortcut,
    _is_domain_path,
    _is_tool_output_dir,
    _is_bare_extension,
    _is_dotted_config_key,
    _is_uppercase_property,
    _is_dotted_method,
    _is_container_image,
)


def is_likely_path(text: str) -> bool:
    """Conservative: exclude everything we know isn't a path, accept the rest."""
    text = text.strip()
    if _looks_like_prose(text):
        return False
    if any(pred(text) for pred in _NON_PATH_PREDICATES):
        return False
    return _looks_pathish(text)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def strip_code_fences(content: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", content)


def extract_backtick_paths(content: str) -> list[str]:
    stripped = strip_code_fences(content)
    return [
        m.group(1).strip().rstrip(",;:")
        for m in re.finditer(r"`([^`\n]+)`", stripped)
        if is_likely_path(m.group(1))
    ]


def _extract_markdown_links(content: str) -> list[str]:
    out: list[str] = []
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", content):
        target = match.group(2).strip()
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        out.append(target.split("#")[0])
    return out


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------


def _under_reference_dir(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root).parts
    except ValueError:
        return False
    return any(part in ("references", "resources", "skills") for part in rel)


def _resolve_ref(ref: str, file_dir: Path, root: Path, git_root_path: Path | None) -> bool:
    clean = re.sub(r":\d+(-\d+)?$", "", ref)
    for base in (file_dir, root, git_root_path):
        if base and (base / clean).exists():
            return True
    return False


def lint_file(path: Path, root: Path, *, git_root_path: Path | None = None) -> Iterator[Finding]:
    content = read_text_safe(path)
    if content is None:
        return
    # extract_backtick_paths already strips code fences — don't double-strip.
    paths = dict.fromkeys(extract_backtick_paths(content))
    in_ref_dir = _under_reference_dir(path, root)

    for ref in paths:
        if _resolve_ref(ref, path.parent, root, git_root_path):
            continue
        if "{{" in ref or "{%" in ref or "*" in ref:
            continue
        if in_ref_dir and ref.startswith("docs/"):
            continue
        yield Finding(
            file=str(path),
            line=0,
            severity=Severity.ERROR,
            code="broken-reference",
            message=f"broken reference `{ref}`",
        )


def _lint_symlinks(root: Path, layout: RepositoryContextLayout) -> Iterator[Finding]:
    for agents in layout.agents_files:
        claude = agents.parent / "CLAUDE.md"
        if claude.is_symlink():
            if not claude.exists():
                yield Finding(
                    file=str(claude),
                    line=0,
                    severity=Severity.ERROR,
                    code="claude-md-broken-symlink",
                    message="broken symlink (target does not exist)",
                )
            elif claude.resolve() != agents.resolve():
                yield Finding(
                    file=str(claude),
                    line=0,
                    severity=Severity.ERROR,
                    code="claude-md-wrong-target",
                    message=f"symlink points to {claude.resolve()}, expected {agents}",
                )
        elif claude.exists():
            yield Finding(
                file=str(claude),
                line=0,
                severity=Severity.ERROR,
                code="claude-md-not-symlink",
                message="is a regular file, must be a symlink to AGENTS.md",
            )


def _lint_docs_indexes(root: Path, layout: RepositoryContextLayout) -> Iterator[Finding]:
    docs_paths = {tree.path for tree in layout.docs_trees}
    for agents in layout.agents_files:
        if agents.parent not in docs_paths:
            continue
        content = read_text_safe(agents) or ""
        referenced = {m.group(1).strip() for m in re.finditer(r"`([^`\n]+)`", content)}
        for md in agents.parent.rglob("*.md"):
            if md.name in ("README.md", "AGENTS.md"):
                continue
            relative_to_docs = md.relative_to(agents.parent)
            if "docs" in relative_to_docs.parts[:-1]:
                continue
            if any(p in EXCLUDED_DIRS for p in md.relative_to(root).parts):
                continue
            rel_to_docs = str(relative_to_docs)
            rel_to_root = str(md.relative_to(root))
            if rel_to_docs in referenced or rel_to_root in referenced:
                continue
            yield Finding(
                file=str(agents),
                line=0,
                severity=Severity.ERROR,
                code="docs-index-incomplete",
                message=f"docs index missing entry for `{rel_to_docs}`",
            )


def _lint_docs_readme_links(root: Path, layout: RepositoryContextLayout) -> Iterator[Finding]:
    for tree in layout.docs_trees:
        readme = tree.path / "README.md"
        if not readme.is_file():
            continue
        content = read_text_safe(readme) or ""
        for link in _extract_markdown_links(content):
            if (readme.parent / link).exists() or (root / link).exists():
                continue
            yield Finding(
                file=str(readme),
                line=0,
                severity=Severity.ERROR,
                code="readme-broken-link",
                message=f"broken link `{link}`",
            )


def _find_context_files(root: Path, layout: RepositoryContextLayout) -> Iterator[Path]:
    yield from layout.agents_files
    for tree in layout.docs_trees:
        docs_dir = tree.path
        for md in sorted(docs_dir.rglob("*.md")):
            relative = md.relative_to(docs_dir)
            if "docs" in relative.parts[:-1]:
                continue
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            yield md


def _context_root_for(path: Path, layout: RepositoryContextLayout) -> Path:
    """Return the nearest contract root that owns a context file."""
    matches = [
        root
        for root in layout.contract_roots
        if path == root or root in path.parents
    ]
    return max(matches, key=lambda root: len(root.parts), default=layout.root)


def lint(root: Path) -> LintResult:
    from ..infra.git import git_root

    root = root.resolve()
    # Materialized commit trees intentionally have no .git directory. In that
    # case the requested validation root is still the repository-scope fallback
    # for references written from the checkout root.
    git_root_path = git_root(root) or root

    layout = discover(root)
    findings: list[Finding] = []
    for path in _find_context_files(root, layout):
        context_root = _context_root_for(path, layout)
        findings.extend(lint_file(path, context_root, git_root_path=git_root_path))
    findings.extend(_lint_symlinks(root, layout))
    findings.extend(_lint_docs_indexes(root, layout))
    findings.extend(_lint_docs_readme_links(root, layout))
    return LintResult(target=str(root), findings=findings)
