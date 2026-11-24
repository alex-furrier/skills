"""Bounded advisory evidence: identical branch-bearing source in different files.

This is a literal source comparison, not an AST clone detector or a quality gate.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from code_health.process import run
from code_health.repository import IGNORED_PARTS, is_test_path

LANG = {
    ".py": "python",
    ".rs": "rust",
    ".go": "go",
    **dict.fromkeys(
        (".js", ".jsx", ".ts", ".tsx", ".mts", ".cts"), "typescript/javascript"
    ),
}
BRANCH = re.compile(r"^(?:if|elif|else if|match|switch|case|except)\b")
EFFECT = re.compile(r"\b(?:return|raise|throw|continue|break)\b")
WORDS = re.compile(r"[A-Za-z_]\w*")
WINDOW = 6
FILE_BYTES = 512_000
TOTAL_BYTES = 12_000_000
MAX_FILES = 2_000
MAX_ANCHORS = 40_000
MAX_COPIES = 6
MAX_PAIRS = 12
MAX_DIFF_FILES = 60
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True, order=True)
class Site:
    path: str
    start: int
    end: int


@dataclass(frozen=True)
class SharedDecision:
    language: str
    left: Site
    right: Site


@dataclass(frozen=True)
class Split:
    language: str
    before: Site
    changed_hunk: Site
    remaining: Site


@dataclass
class SharedEvidence:
    scope: str
    status: str = "ok"
    reviewed_files: int = 0
    skipped: dict[str, int] = field(default_factory=dict)
    matches: list[SharedDecision] = field(default_factory=list)
    one_sided_edits: list[Split] = field(default_factory=list)


def _keys(lines: list[str]):
    branches = [bool(BRANCH.match(s.lstrip())) for s in lines]
    effects = [bool(EFFECT.search(s)) for s in lines]
    words = [len(WORDS.findall(s)) for s in lines]
    for i in range(len(lines) - WINDOW + 1):
        end = i + WINDOW
        if (
            not any(branches[i:end])
            or not any(effects[i:end])
            or sum(words[i:end]) < 16
        ):
            continue
        block = lines[i:end]
        if sum(w >= 2 for w in words[i:end]) < 3:
            continue
        if any(
            s.lstrip().startswith(("#", "//", "/*", "*", '"""', "'''")) for s in block
        ):
            continue
        # Keep indentation, case, identifiers, literals, comments and braces intact.
        yield hashlib.sha256("\n".join(block).encode()).digest(), i + 1


def _git(args, root):
    try:
        return run(["git", "--literal-pathspecs", *args], cwd=root)
    except (RuntimeError, UnicodeError):
        return None


def _hunks(root: Path, path: str, base: str) -> list[tuple[int, int, int, int]] | None:
    result = _git(
        [
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            "--unified=0",
            base,
            "--",
            path,
        ],
        root,
    )
    if result is None or result.returncode:
        return None
    intervals = []
    for line in result.stdout.splitlines():
        if match := HUNK.match(line):
            intervals.append(
                (int(match[1]), int(match[2] or 1), int(match[3]), int(match[4] or 1))
            )
    return intervals


class _Budget:
    """Shared bounds for candidate *and* baseline evidence."""

    def __init__(self):
        self.bytes = self.files = self.windows = 0
        self.gaps = Counter()
        self.exhausted = False

    def lines(self, root, name):
        path = root / name
        try:
            if path.resolve() != path:
                self.gaps["symbolic or outside path"] += 1
                return None
            if not path.is_file():
                return None
            size = path.stat().st_size
            if size > FILE_BYTES:
                self.gaps["oversize file"] += 1
                return None
            if self.bytes + size > TOTAL_BYTES or self.files >= MAX_FILES:
                self.gaps["repository budget reached"] += 1
                self.exhausted = True
                return None
            self.bytes += size
            self.files += 1
            with path.open("rb") as handle:
                data = handle.read(FILE_BYTES + 1)
            if len(data) > FILE_BYTES or b"\0" in data:
                self.gaps["binary or oversize file"] += 1
                return None
            if any(
                x in data[:512].lower()
                for x in (b"@generated", b"code generated", b"do not edit")
            ):
                self.gaps["generated header"] += 1
                return None
            return data.decode().splitlines()
        except (OSError, UnicodeError, RuntimeError):
            self.gaps["unreadable file"] += 1
            return None

    def keys(self, lines):
        for digest, start in _keys(lines):
            if self.windows >= MAX_ANCHORS:
                self.gaps["window budget reached"] += 1
                self.exhausted = True
                return
            self.windows += 1
            yield digest, start


def _store(bucket, item):
    # Keep one sentinel beyond the limit, so frequent excerpts remain suppressed.
    if len(bucket) <= MAX_COPIES:
        bucket.append(item)


def _before(name, language, old, hunks, present, displaced, budget):
    for key, start in budget.keys(old):
        if key in present:
            continue
        for old_start, removed, new_start, added in hunks:
            if not removed or not added:
                continue
            lo = max(old_start, start)
            hi = min(old_start + removed - 1, start + WINDOW - 1)
            if lo > hi:
                continue
            # Changing only a nearby comment or declaration isn't changing the guard/action.
            if not any(
                BRANCH.match(s.lstrip()) or EFFECT.search(s) for s in old[lo - 1 : hi]
            ):
                continue
            _store(
                displaced[language, key],
                (
                    Site(name, start, start + WINDOW - 1),
                    Site(name, new_start, new_start + added - 1),
                ),
            )
            break


def collect(
    root: Path,
    scope: Path,
    changed: set[str] | None,
    base: str | None = None,
    before_root: Path | None = None,
) -> SharedEvidence:
    """Compare tracked regular files within scope, including unchanged peers."""
    root = root.resolve()
    if before_root is not None:
        before_root = before_root.resolve()
    evidence = SharedEvidence(
        "pairs intersecting added or modified lines"
        if changed is not None
        else "all file pairs"
    )
    if changed is not None and base:
        # NUL-delimited names avoid git quoting a modified path as an unchanged peer.
        names = _git(
            [
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--name-only",
                "-z",
                base,
                "--",
                scope.as_posix(),
            ],
            root,
        )
        if names is None or names.returncode:
            return _finish(evidence, {"changed file list unavailable": 1})
        changed = set(filter(None, names.stdout.split("\0")))
    if changed == set():
        return evidence
    listed = _git(["ls-files", "--cached", "-z", "--", scope.as_posix()], root)
    if listed is None or listed.returncode:
        return _finish(evidence, {"tracked file list unavailable": 1})
    budget = _Budget()
    groups, displaced = defaultdict(list), defaultdict(list)
    ranges = {}
    for name in sorted(set(listed.stdout.split("\0"))):
        if budget.exhausted:
            break
        p = Path(name)
        language = LANG.get(p.suffix)
        if not language or p.is_absolute() or ".." in p.parts or is_test_path(p):
            continue
        if set(p.parts) & (IGNORED_PARTS | {"fixtures", "generated", "__generated__"}):
            continue
        lines = budget.lines(root, name)
        if lines is None:
            continue
        evidence.reviewed_files += 1
        keys = list(budget.keys(lines))
        for key, pos in keys:
            _store(groups[language, key], (name, pos))
        if changed is None or name not in changed or budget.exhausted:
            continue
        if len(ranges) >= MAX_DIFF_FILES:
            budget.gaps["changed-file diff budget"] += 1
            continue
        hunks = _hunks(root, name, base) if base else None
        if hunks is None or len(hunks) > 128:
            budget.gaps["diff unavailable or over hunk budget"] += 1
            continue
        ranges[name] = [(c, c + n - 1) for _, _, c, n in hunks if n]
        if before_root and any(k and n for _, k, _, n in hunks):
            old = budget.lines(before_root, name)
            if old is not None:
                _before(
                    name, language, old, hunks, {k for k, _ in keys}, displaced, budget
                )
    return _report(evidence, groups, ranges, displaced, budget.gaps, changed)


def _report(evidence, groups, ranges, displaced, counts, changed):
    best = {}
    # Keep one representative per file pair; repeated boilerplate is not a vote.
    for (language, _), group in groups.items():
        if len(group) > MAX_COPIES:
            counts["frequent window suppressed"] += 1
            continue
        for j, (left, i) in enumerate(group):
            for right, k in group[j + 1 :]:
                if left == right:
                    continue
                if changed is not None and not any(
                    lo <= start + WINDOW - 1 and start <= hi
                    for path, start in ((left, i), (right, k))
                    for lo, hi in ranges.get(path, ())
                ):
                    continue
                candidate = SharedDecision(
                    language,
                    Site(left, i, i + WINDOW - 1),
                    Site(right, k, k + WINDOW - 1),
                )
                key = (left, right)
                if key not in best or candidate.left.start < best[key].left.start:
                    best[key] = candidate
    # A former fragment must disappear in the changed file and still exist at
    # an untouched sibling. A deletion, rename, or unrelated edit alone is not a split.
    splits = {}
    for (language, key), originals in displaced.items():
        current = groups.get((language, key), [])
        if not current or len(current) + len(originals) > MAX_COPIES:
            continue
        for original, hunk in originals:
            for path, start in current:
                if changed is None or path in changed:
                    continue
                pair = (original.path, path)
                if pair not in splits or original.start < splits[pair].before.start:
                    splits[pair] = Split(
                        language, original, hunk, Site(path, start, start + WINDOW - 1)
                    )
    evidence.one_sided_edits = [splits[k] for k in sorted(splits)[:MAX_PAIRS]]
    if len(splits) > MAX_PAIRS:
        counts["additional file pairs omitted"] += len(splits) - MAX_PAIRS
    candidates = [best[key] for key in sorted(best)]
    evidence.matches = candidates[:MAX_PAIRS]
    if len(candidates) > MAX_PAIRS:
        counts["additional file pairs omitted"] += len(candidates) - MAX_PAIRS
    return _finish(evidence, counts)


def _finish(evidence, counts):
    evidence.skipped = dict(sorted(counts.items()))
    if any(
        k
        not in {
            "generated header",
            "frequent window suppressed",
            "additional file pairs omitted",
        }
        for k in counts
    ):
        evidence.status = "partial"
    return evidence
