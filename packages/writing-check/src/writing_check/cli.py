#!/usr/bin/env python3
"""Read-only source-bound advisory writing evidence with optional Vale JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

EXIT_CLEAN, EXIT_FINDINGS, EXIT_INPUT, EXIT_UNAVAILABLE, EXIT_EXECUTION = range(5)
ROOT = pathlib.Path(__file__).resolve().parent
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
SENTENCE = re.compile(r"[.!?]+")


class PolicyError(ValueError):
    """Raised when the bundled public policy closure is not intact."""


class UnknownProfile(ValueError):
    """Raised for the existing public input-error profile boundary."""

    def __init__(self, profiles: list[str]) -> None:
        self.profiles = profiles


def policy_file(root: pathlib.Path, relative: str) -> pathlib.Path:
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise PolicyError(f"missing policy file: {relative}")
    return path


def load_policy(profile: str) -> tuple[dict[str, Any], str]:
    vale = ROOT / "vale"
    try:
        manifest_bytes = policy_file(vale, "profiles.json").read_bytes()
        lock_bytes = policy_file(vale, "upstream-lock.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        lock = json.loads(lock_bytes)
        if not isinstance(lock, dict):
            raise PolicyError("policy lock has an invalid root")
    except (OSError, json.JSONDecodeError, PolicyError) as error:
        raise PolicyError(f"invalid policy metadata: {error}") from error
    profiles, rules, config = manifest.get("profiles"), manifest.get("rules"), manifest.get("config")
    if not isinstance(profiles, dict) or not isinstance(rules, dict):
        raise PolicyError("policy manifest has an invalid profile or rule inventory")
    if not isinstance(config, dict) or config.get("path") != ".vale.ini" or not isinstance(config.get("sha256"), str):
        raise PolicyError("invalid policy config metadata")
    config_bytes = policy_file(vale, config["path"]).read_bytes()
    if hashlib.sha256(config_bytes).hexdigest() != config["sha256"]:
        raise PolicyError("policy config digest mismatch")
    if profile not in profiles:
        raise UnknownProfile(sorted(profiles))
    selected = profiles[profile]
    if not isinstance(selected, dict) or not isinstance(selected.get("policy"), str):
        raise PolicyError(f"invalid policy profile: {profile}")
    upstream = lock.get("upstream")
    if not isinstance(upstream, dict) or not isinstance(upstream.get("license_file"), str) or not isinstance(upstream.get("license_sha256"), str):
        raise PolicyError("invalid policy license metadata")
    license_path = policy_file(vale, upstream["license_file"])
    license_bytes = license_path.read_bytes()
    if hashlib.sha256(license_bytes).hexdigest() != upstream["license_sha256"]:
        raise PolicyError("policy license digest mismatch")
    declared: set[str] = set()
    selected_files: list[tuple[str, bytes]] = []
    for name, metadata in sorted(rules.items()):
        if not isinstance(name, str) or not isinstance(metadata, dict):
            raise PolicyError("invalid policy rule metadata")
        relative, digest, rule_profiles = metadata.get("path"), metadata.get("sha256"), metadata.get("profiles")
        if not isinstance(relative, str) or not isinstance(digest, str) or not isinstance(rule_profiles, list):
            raise PolicyError(f"invalid policy rule metadata: {name}")
        if profile not in rule_profiles or not all(isinstance(item, str) for item in rule_profiles):
            raise PolicyError(f"invalid policy rule profile closure: {name}")
        path = policy_file(vale, relative)
        contents = path.read_bytes()
        if hashlib.sha256(contents).hexdigest() != digest:
            raise PolicyError(f"policy rule digest mismatch: {relative}")
        declared.add(relative)
        selected_files.append((relative, contents))
    actual = {path.relative_to(vale).as_posix() for path in (vale / "styles" / "GoogleDocs").glob("*.yml")}
    if not declared or actual != declared:
        raise PolicyError("policy rule inventory mismatch")
    identity = [(".vale.ini", config_bytes), ("profiles.json", manifest_bytes), ("upstream-lock.json", lock_bytes), (upstream["license_file"], license_bytes), *selected_files]
    digest = hashlib.sha256()
    for relative, contents in identity:
        digest.update(relative.encode("utf-8")); digest.update(b"\0"); digest.update(contents); digest.update(b"\0")
    return selected, digest.hexdigest()


def source(path: str) -> tuple[str, str, bytes]:
    if path == "-":
        return "stdin", "stdin", sys.stdin.buffer.read()
    file = pathlib.Path(path).expanduser().resolve()
    if not file.is_file():
        raise OSError(f"input is not a regular file: {file}")
    return "file", str(file), file.read_bytes()


def prose_parts(text: str) -> tuple[str, str]:
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


def readability(text: str, profile: str) -> dict[str, Any]:
    included, excluded = prose_parts(text)
    words, excluded_words = WORD.findall(included), WORD.findall(excluded)
    sentences = len(SENTENCE.findall(included))
    if profile == "commit":
        return {"status": "disabled", "words": len(words), "sentences": sentences, "targets": None}
    if profile in {"readme", "technical-doc-reference"} and len(excluded_words) > len(words):
        return {"status": "composition_limited", "words": len(words), "sentences": sentences, "excluded_words": len(excluded_words), "targets": None}
    minimum_words, minimum_sentences = (200, 8) if profile in {"pr-description", "user-facing-response"} else (300, 8)
    state = "insufficient_sample" if len(words) < 100 or sentences < 5 else "small_sample" if len(words) < minimum_words or sentences < minimum_sentences else "normal"
    result: dict[str, Any] = {"status": state, "words": len(words), "sentences": sentences, "targets": {"fre_min": 55, "fk_max": 10} if state == "normal" else None}
    if state == "normal":
        syllables = sum(max(1, len(re.findall(r"[aeiouy]+", word.lower()))) for word in words)
        result["flesch_reading_ease"] = round(206.835 - 1.015 * len(words) / sentences - 84.6 * syllables / len(words), 2)
        result["flesch_kincaid_grade"] = round(.39 * len(words) / sentences + 11.8 * syllables / len(words) - 15.59, 2)
    return result


def normalize_vale(raw: str) -> list[dict[str, Any]]:
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid Vale JSON: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("invalid Vale JSON root: expected an object")
    alerts: list[dict[str, Any]] = []
    for path, items in sorted(document.items()):
        if not isinstance(items, list):
            raise ValueError(f"invalid Vale alerts for {path}: expected a list")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"invalid Vale alert for {path}: expected an object")
            check, message, line, span = item.get("Check"), item.get("Message"), item.get("Line"), item.get("Span")
            if not isinstance(check, str) or not check or not isinstance(message, str) or not message:
                raise ValueError(f"invalid Vale alert fields for {path}")
            if isinstance(line, bool) or not isinstance(line, int) or line < 1:
                raise ValueError(f"invalid Vale alert line for {path}")
            if not isinstance(span, list) or len(span) != 2 or any(isinstance(value, bool) or not isinstance(value, int) for value in span) or span[0] < 1 or span[1] < span[0]:
                raise ValueError(f"invalid Vale alert span for {path}")
            alerts.append({"source": "vale", "rule": check, "message": message, "severity": "suggestion", "line": line, "span": span, "path": path})
    return alerts


def print_record(record: dict[str, Any]) -> None:
    print(json.dumps(record, indent=2))


def resolve_vale() -> str | None:
    """Prefer Vale installed beside this command's Python interpreter."""
    environment_vale = pathlib.Path(sys.executable).parent / "vale"
    if environment_vale.is_file() and os.access(environment_vale, os.X_OK):
        return str(environment_vale)
    return shutil.which("vale")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("input")
    args = parser.parse_args()
    try:
        selected_policy, policy_digest = load_policy(args.profile)
    except UnknownProfile as error:
        print_record({"schema": 3, "status": "input_error", "error": {"code": "unknown_profile", "message": f"unknown profile: {args.profile}"}, "allowed_profiles": error.profiles})
        return EXIT_INPUT
    except PolicyError as error:
        print_record({"schema": 3, "status": "execution_error", "error": {"code": "policy_validation_failed", "message": str(error)}})
        return EXIT_EXECUTION
    try:
        kind, identifier, data = source(args.input)
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print_record({"schema": 3, "status": "input_error", "profile": args.profile, "error": {"code": "invalid_utf8" if isinstance(error, UnicodeDecodeError) else "input_read_failed", "message": str(error)}})
        return EXIT_INPUT
    record: dict[str, Any] = {"schema": 3, "status": None, "advisory": True, "profile": args.profile, "policy": {"name": selected_policy["policy"], "sha256": policy_digest}, "source": {"kind": kind, "identifier": identifier, "encoding": "utf-8", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "text": text}, "readability": readability(text, args.profile), "alerts": [], "vale": {}}
    vale = resolve_vale()
    if not vale:
        record.update(status="unavailable", vale={"status": "unavailable", "reason": "Vale was not found; no substitute was run."})
        print_record(record)
        return EXIT_UNAVAILABLE
    version_argv = [vale, "--version"]
    try:
        version_run = subprocess.run(version_argv, capture_output=True, text=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        version: dict[str, Any] = {"argv": version_argv}
        if isinstance(error, subprocess.TimeoutExpired):
            if error.stdout is not None:
                version["stdout"] = error.stdout.decode("utf-8", errors="replace")
            if error.stderr is not None:
                version["stderr"] = error.stderr.decode("utf-8", errors="replace")
        record.update(status="execution_error", vale={"status": "execution_error", "version": version, "error": str(error)})
        print_record(record)
        return EXIT_EXECUTION
    try:
        version_stdout, version_stderr = version_run.stdout.decode("utf-8"), version_run.stderr.decode("utf-8")
    except UnicodeDecodeError as error:
        version = {"argv": version_argv, "exit": version_run.returncode, "stdout": version_run.stdout.decode("utf-8", errors="replace"), "stderr": version_run.stderr.decode("utf-8", errors="replace")}
        record.update(status="execution_error", vale={"status": "execution_error", "version": version, "error": f"invalid UTF-8 in Vale version output: {error}"})
        print_record(record)
        return EXIT_EXECUTION
    version = {"argv": version_argv, "exit": version_run.returncode, "stdout": version_stdout, "stderr": version_stderr}
    if version_run.returncode != 0:
        record.update(status="execution_error", vale={"status": "execution_error", "version": version, "error": f"Vale version exited {version_run.returncode}"})
        print_record(record)
        return EXIT_EXECUTION
    lint_argv = [vale, "--no-global", f"--config={ROOT / 'vale' / '.vale.ini'}", "--no-exit", "--output=JSON", "--ext=.md", "-"]
    lint: dict[str, Any] = {"argv": lint_argv}
    record["vale"] = {"status": "ran", "version": version, "lint": lint}
    try:
        lint_run = subprocess.run(lint_argv, input=data, capture_output=True, text=False, timeout=30)
        try:
            stdout, stderr = lint_run.stdout.decode("utf-8"), lint_run.stderr.decode("utf-8")
        except UnicodeDecodeError as error:
            lint = {"argv": lint_argv, "exit": lint_run.returncode, "stdout": lint_run.stdout.decode("utf-8", errors="replace"), "stderr": lint_run.stderr.decode("utf-8", errors="replace")}
            record["vale"] = {"status": "ran", "version": version, "lint": lint, **lint}
            raise ValueError(f"invalid UTF-8 in Vale output: {error}") from error
        lint = {"argv": lint_argv, "exit": lint_run.returncode, "stdout": stdout, "stderr": stderr}
        record["vale"] = {"status": "ran", "version": version, "lint": lint, **lint}
        if lint_run.returncode not in (0, 1):
            raise RuntimeError(f"Vale exited {lint_run.returncode}")
        record["alerts"] = normalize_vale(stdout)
    except (OSError, UnicodeDecodeError, subprocess.TimeoutExpired, ValueError, RuntimeError) as error:
        if isinstance(error, subprocess.TimeoutExpired):
            if error.stdout is not None:
                lint["stdout"] = error.stdout.decode("utf-8", errors="replace")
            if error.stderr is not None:
                lint["stderr"] = error.stderr.decode("utf-8", errors="replace")
        vale_record = record.get("vale", {})
        vale_record.update(status="execution_error", version=version, error=str(error))
        record.update(status="execution_error", vale=vale_record)
        print_record(record)
        return EXIT_EXECUTION
    record["status"] = "findings" if record["alerts"] else "no_findings"
    print_record(record)
    return EXIT_FINDINGS if record["alerts"] else EXIT_CLEAN


def entrypoint() -> None:
    """Run the installed Writing Check command."""
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
