#!/usr/bin/env python3
"""Read-only source-bound advisory writing evidence with optional Vale JSON."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys

EXIT_CLEAN, EXIT_FINDINGS, EXIT_INPUT, EXIT_UNAVAILABLE, EXIT_EXECUTION = range(5)
ROOT = pathlib.Path(__file__).resolve().parents[1]
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
SENTENCE = re.compile(r"[.!?]+")


def load_profiles():
    raw = (ROOT / "vale" / "profiles.json").read_bytes()
    data = json.loads(raw)
    return data["profiles"], hashlib.sha256(raw).hexdigest()


def source(path: str):
    if path == "-":
        data = sys.stdin.buffer.read()
        return "stdin", "stdin", data
    file = pathlib.Path(path).expanduser().resolve()
    if not file.is_file():
        raise OSError(f"input is not a regular file: {file}")
    return "file", str(file), file.read_bytes()


def prose_parts(text: str):
    included, excluded = [], []
    fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            continue
        cleaned = re.sub(r"`[^`]*`|https?://\S+|!\[[^]]*\]\([^)]*\)", " ", line)
        cleaned = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", cleaned)
        if fence or line.startswith("---") or re.match(r"^\s*(#|<!--|<[^>]+>)", line):
            excluded.append(cleaned)
        elif "|" in line or re.match(r"^\s*[-*+]\s+\S{1,4}\s*$", line):
            excluded.append(cleaned)
        else:
            included.append(cleaned)
    return " ".join(included), " ".join(excluded)


def readability(text: str, profile: str):
    included, excluded = prose_parts(text)
    words = WORD.findall(included)
    excluded_words = WORD.findall(excluded)
    sentences = len(SENTENCE.findall(included))
    if profile == "commit":
        return {"status": "disabled", "words": len(words), "sentences": sentences, "targets": None}
    if profile in {"readme", "technical-doc-reference"} and len(excluded_words) > len(words):
        return {"status": "composition_limited", "words": len(words), "sentences": sentences, "excluded_words": len(excluded_words), "targets": None}
    minimum_words, minimum_sentences = (200, 8) if profile in {"pr-description", "user-facing-response"} else (300, 8)
    state = "insufficient_sample" if len(words) < 100 or sentences < 5 else "small_sample" if len(words) < minimum_words or sentences < minimum_sentences else "normal"
    result = {"status": state, "words": len(words), "sentences": sentences, "targets": {"fre_min": 55, "fk_max": 10} if state == "normal" else None}
    if state == "normal":
        syllables = sum(max(1, len(re.findall(r"[aeiouy]+", word.lower()))) for word in words)
        result["flesch_reading_ease"] = round(206.835 - 1.015 * len(words) / sentences - 84.6 * syllables / len(words), 2)
        result["flesch_kincaid_grade"] = round(.39 * len(words) / sentences + 11.8 * syllables / len(words) - 15.59, 2)
    return result


def normalize_vale(raw: str):
    try:
        document = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid Vale JSON: {exc}") from exc
    alerts = []
    def add(item, path=""):
        if isinstance(item, dict):
            alerts.append({"source": "vale", "rule": str(item.get("Check") or item.get("Rule") or "Vale"), "message": str(item.get("Message") or "Vale observation"), "severity": "suggestion", "line": item.get("Line") or item.get("line"), "span": item.get("Span") or item.get("span"), "path": path})
    if isinstance(document, dict):
        for path, items in document.items():
            if isinstance(items, list):
                for item in items: add(item, path)
            elif isinstance(items, dict): add(items, path)
    elif isinstance(document, list):
        for item in document: add(item)
    return alerts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("input")
    args = parser.parse_args()
    profiles, policy_digest = load_profiles()
    if args.profile not in profiles:
        print(json.dumps({"schema": 3, "status": "input_error", "error": {"code": "unknown_profile", "message": f"unknown profile: {args.profile}"}, "allowed_profiles": sorted(profiles)}))
        return EXIT_INPUT
    try:
        kind, identifier, data = source(args.input)
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"schema": 3, "status": "input_error", "profile": args.profile, "error": {"code": "invalid_utf8" if isinstance(exc, UnicodeDecodeError) else "input_read_failed", "message": str(exc)}}))
        return EXIT_INPUT
    record = {"schema": 3, "status": None, "advisory": True, "profile": args.profile, "policy": {"name": profiles[args.profile]["policy"], "sha256": policy_digest}, "source": {"kind": kind, "identifier": identifier, "encoding": "utf-8", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "text": text}, "readability": readability(text, args.profile), "alerts": [], "vale": {}}
    vale = shutil.which("vale")
    if not vale:
        record.update(status="unavailable")
        record["vale"] = {"status": "unavailable", "reason": "Vale was not found; no substitute was run."}
        print(json.dumps(record, indent=2)); return EXIT_UNAVAILABLE
    try:
        run = subprocess.run([vale, f"--config={ROOT / 'vale' / '.vale.ini'}", "--no-exit", "--output=JSON", args.input], capture_output=True, text=True, timeout=30)
        if run.returncode not in (0, 1): raise RuntimeError(f"Vale exited {run.returncode}")
        record["vale"] = {"status": "ran", "argv": [vale, f"--config={ROOT / 'vale' / '.vale.ini'}", "--no-exit", "--output=JSON", args.input], "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
        record["alerts"] = normalize_vale(run.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError, RuntimeError) as exc:
        record.update(status="execution_error")
        record["vale"] = {"status": "execution_error", "error": str(exc)}
        print(json.dumps(record, indent=2)); return EXIT_EXECUTION
    record["status"] = "findings" if record["alerts"] else "no_findings"
    print(json.dumps(record, indent=2))
    return EXIT_FINDINGS if record["alerts"] else EXIT_CLEAN

if __name__ == "__main__":
    raise SystemExit(main())
