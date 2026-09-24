#!/usr/bin/env python3
"""Fail closed on release routing and the two distributable archive payloads."""
from __future__ import annotations

import argparse
from configparser import ConfigParser
from email.parser import BytesParser
import pathlib
import re
import tarfile
import tomllib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGES = {
    "context-engineering": ("safurrier-context-engineering", "context_engineering"),
    "writing-check": ("safurrier-writing-check", "writing_check"),
}
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def release_identity(package: str, ref: str, tag: str) -> tuple[str, str, str]:
    name, module = PACKAGES[package]
    prefix = f"{package}-v"
    if not tag.startswith(prefix) or not VERSION.fullmatch(tag[len(prefix):]):
        raise ValueError(f"tag must match {prefix}X.Y.Z")
    if ref != f"refs/tags/{tag}":
        raise ValueError("release ref and tag do not match")
    version = tag[len(prefix):]
    metadata = tomllib.loads((ROOT / "packages" / package / "pyproject.toml").read_text())
    if metadata["project"]["name"] != name or metadata["project"]["version"] != version:
        raise ValueError("release tag does not match project name and version")
    return name, module, version


def check_members(members: dict[str, bytes], name: str, module: str, version: str, wheel: bool) -> None:
    normalized = name.replace("-", "_")
    base = "" if wheel else f"{normalized}-{version}/"
    package_root = f"{module}/" if wheel else f"{base}src/{module}/"
    dist_info = f"{normalized}-{version}.dist-info/"
    allowed = (package_root,)
    for path in members:
        parts = pathlib.PurePosixPath(path).parts
        if path.startswith("/") or any(part in (".", "..") for part in parts) or "\\" in path:
            raise ValueError(f"unsafe archive path: {path}")
        if not path.startswith(allowed) and path not in (
            ("provenance.json", f"{dist_info}METADATA", f"{dist_info}WHEEL", f"{dist_info}RECORD", f"{dist_info}entry_points.txt", f"{dist_info}licenses/LICENSE")
            if wheel else (f"{base}provenance.json", f"{base}LICENSE", f"{base}README.md", f"{base}pyproject.toml", f"{base}PKG-INFO", f"{base}.gitignore")
        ):
            raise ValueError(f"unexpected archive member: {path}")
    required = {
        "provenance.json" if wheel else f"{base}provenance.json",
        f"{dist_info}licenses/LICENSE" if wheel else f"{base}LICENSE",
        f"{package_root}__init__.py",
        f"{package_root}cli/dispatch.py" if module == "context_engineering" else f"{package_root}cli.py",
        f"{dist_info}METADATA" if wheel else f"{base}PKG-INFO",
    }
    if wheel:
        required.add(f"{dist_info}entry_points.txt")
    if module == "writing_check":
        if not wheel:
            required.add(f"{base}README.md")
        required |= {f"{package_root}vale/{item}" for item in (".vale.ini", "profiles.json", "upstream-lock.json", "vendor/Google-LICENSE")}
        if not any(path.startswith(f"{package_root}vale/styles/GoogleDocs/") and path.endswith(".yml") for path in members):
            raise ValueError("Vale rules missing")
    if required - members.keys():
        raise ValueError(f"required archive members missing: {sorted(required - members.keys())}")
    source = ROOT / "packages" / ("context-engineering" if module == "context_engineering" else "writing-check") / "src" / module
    expected = {
        f"{package_root}{path.relative_to(source).as_posix()}"
        for path in source.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    actual = {path for path in members if path.startswith(package_root)}
    if actual != expected:
        raise ValueError(f"package payload differs from source: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    for path in actual:
        if members[path] != (source / path.removeprefix(package_root)).read_bytes():
            raise ValueError(f"package payload differs from source: {path}")
    project = ROOT / "packages" / ("context-engineering" if module == "context_engineering" else "writing-check")
    for archive_path, source_path in (
        (("provenance.json" if wheel else f"{base}provenance.json"), project / "provenance.json"),
        ((f"{dist_info}licenses/LICENSE" if wheel else f"{base}LICENSE"), project / "LICENSE"),
    ):
        if members[archive_path] != source_path.read_bytes():
            raise ValueError(f"archive notice differs from source: {archive_path}")
    if not wheel and members[f"{base}pyproject.toml"] != (project / "pyproject.toml").read_bytes():
        raise ValueError("sdist project metadata differs from source")
    if not wheel and module == "writing_check" and members[f"{base}README.md"] != (project / "README.md").read_bytes():
        raise ValueError("sdist README differs from source")
    project_metadata = tomllib.loads((project / "pyproject.toml").read_text())["project"]
    parsed = BytesParser().parsebytes(members[f"{dist_info}METADATA" if wheel else f"{base}PKG-INFO"])
    if parsed["Name"] != name or parsed["Version"] != version:
        raise ValueError("archive metadata name/version mismatch")
    if sorted(parsed.get_all("Requires-Dist", [])) != sorted(project_metadata.get("dependencies", [])):
        raise ValueError("archive dependencies differ from project metadata")
    if wheel:
        entries = ConfigParser(interpolation=None)
        entries.read_string(members[f"{dist_info}entry_points.txt"].decode("utf-8"))
        if dict(entries.items("console_scripts")) != project_metadata["scripts"] or entries.sections() != ["console_scripts"]:
            raise ValueError("wheel entry points differ from project metadata")


def check_artifacts(dist: pathlib.Path, name: str, module: str, version: str) -> None:
    normalized = name.replace("-", "_")
    wheel_name = f"{normalized}-{version}-py3-none-any.whl"
    sdist_name = f"{normalized}-{version}.tar.gz"
    if not dist.is_dir() or {p.name for p in dist.iterdir()} != {wheel_name, sdist_name}:
        raise ValueError("dist must contain only the expected wheel and sdist")
    with zipfile.ZipFile(dist / wheel_name) as archive:
        infos = archive.infolist()
        if len({info.filename for info in infos}) != len(infos) or any(info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000 for info in infos):
            raise ValueError("wheel contains duplicate, directory, or symlink entries")
        check_members({info.filename: archive.read(info) for info in infos}, name, module, version, True)
    with tarfile.open(dist / sdist_name, "r:gz") as archive:
        infos = archive.getmembers()
        files = [info for info in infos if info.isfile()]
        if len({info.name for info in infos}) != len(infos) or any(not info.isfile() and not info.isdir() for info in infos):
            raise ValueError("sdist contains duplicate or non-regular entries")
        for info in infos:
            path = info.name
            parts = pathlib.PurePosixPath(path).parts
            base = f"{normalized}-{version}"
            if path.startswith("/") or "\\" in path or any(part in (".", "..") for part in parts) or not (path == base or path.startswith(f"{base}/")):
                raise ValueError(f"unsafe archive path: {path}")
        check_members({info.name: archive.extractfile(info).read() for info in files}, name, module, version, False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", choices=PACKAGES)
    parser.add_argument("ref")
    parser.add_argument("tag")
    parser.add_argument("--dist", type=pathlib.Path)
    args = parser.parse_args()
    name, module, version = release_identity(args.package, args.ref, args.tag)
    if args.dist is not None:
        check_artifacts(args.dist, name, module, version)
    print(f"Validated {name} {version}" + (" artifacts" if args.dist is not None else " tag"))


if __name__ == "__main__":
    main()
