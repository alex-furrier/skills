"""Offline release routing and artifact safety checks."""
import importlib.util
import pathlib
import shutil
import subprocess
import tarfile
import io
import json
import zipfile

import pytest

ROOT = pathlib.Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("check_publish", ROOT / "scripts/check_publish.py")
assert spec and spec.loader
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


@pytest.mark.parametrize(
    "package,version,distribution",
    [("context-engineering", "2.6.0", "context-engineering-cli"),
     ("writing-check", "1.0.0", "writing-check-cli")],
)
def test_release_routing_and_artifacts(package, version, distribution, tmp_path):
    tag = f"{package}-v{version}"
    name, module, parsed_version = publish.release_identity(package, f"refs/tags/{tag}", tag)
    assert name == distribution
    assert parsed_version == version
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages" / package), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    publish.check_artifacts(dist, name, module, version)
    (dist / "unrelated.whl").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="only the expected"):
        publish.check_artifacts(dist, name, module, version)
    (dist / "unrelated.whl").unlink()
    wheel = next(dist.glob("*.whl"))
    original_wheel = tmp_path / "original.whl"
    shutil.copyfile(wheel, original_wheel)
    altered = tmp_path / "altered.whl"
    with zipfile.ZipFile(wheel) as source, zipfile.ZipFile(altered, "w") as target:
        for member in source.infolist():
            target.writestr(member, source.read(member))
        target.writestr("private/session.txt", "do not publish")
    shutil.copyfile(altered, wheel)
    with pytest.raises(ValueError, match="unexpected archive member"):
        publish.check_artifacts(dist, name, module, version)
    shutil.copyfile(original_wheel, wheel)
    sdist = next(dist.glob("*.tar.gz"))
    with tarfile.open(sdist, "w:gz") as archive:
        data = b"outside source"
        info = tarfile.TarInfo("../private.txt")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    with pytest.raises(ValueError, match="unsafe archive path"):
        publish.check_artifacts(dist, name, module, version)


@pytest.mark.parametrize(
    "package,version,missing",
    [
        ("context-engineering", "2.6.0", "pyproject.toml"),
        ("context-engineering", "2.6.0", ".gitignore"),
        ("context-engineering", "2.6.0", "README.md"),
        ("writing-check", "1.0.0", ".gitignore"),
        ("writing-check", "1.0.0", "README.md"),
        ("writing-check", "1.0.0", "pyproject.toml"),
        ("writing-check", "1.0.0", "provenance.json"),
        ("context-engineering", "2.6.0", "src/context_engineering/"),
        ("writing-check", "1.0.0", "src/writing_check/"),
    ],
)
def test_shipped_source_requires_package_provenance(package, version, missing, tmp_path):
    name, module = publish.PACKAGES[package]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages" / package), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    sdist = next(dist.glob("*.tar.gz"))
    with tarfile.open(sdist, "r:gz") as archive:
        members = {item.name: archive.extractfile(item).read() for item in archive if item.isfile()}
    base = f"{name.replace('-', '_')}-{version}/"
    if package == "context-engineering" and missing == "README.md":
        members[f"{base}README.md"] = b"new source-authored README\n"
    inventory = json.loads(members[f"{base}provenance.json"])
    inventory["entries"] = [
        entry for entry in inventory["entries"]
        if entry.get("path", entry.get("path_prefix")) != missing
    ]
    members[f"{base}provenance.json"] = json.dumps(inventory).encode()
    with pytest.raises(ValueError, match="package provenance missing shipped source path"):
        publish.check_members(members, name, module, version, False)


def test_sdist_gitignore_must_match_repository_source(tmp_path):
    name, module, version = "context-engineering-cli", "context_engineering", "2.6.0"
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/context-engineering"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with tarfile.open(next(dist.glob("*.tar.gz")), "r:gz") as archive:
        members = {item.name: archive.extractfile(item).read() for item in archive if item.isfile()}
    base = f"{name.replace('-', '_')}-{version}/"
    members[f"{base}.gitignore"] = b"unreviewed build exclusion\n"
    with pytest.raises(ValueError, match="sdist .gitignore differs from source"):
        publish.check_members(members, name, module, version, False)


def test_package_provenance_rejects_boolean_schema(tmp_path):
    name, module, version = "context-engineering-cli", "context_engineering", "2.6.0"
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/context-engineering"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with tarfile.open(next(dist.glob("*.tar.gz")), "r:gz") as archive:
        members = {item.name: archive.extractfile(item).read() for item in archive if item.isfile()}
    base = f"{name.replace('-', '_')}-{version}/"
    inventory = json.loads(members[f"{base}provenance.json"])
    inventory["schema"] = True
    members[f"{base}provenance.json"] = json.dumps(inventory).encode()
    with pytest.raises(ValueError, match="invalid package provenance entries"):
        publish.check_members(members, name, module, version, False)


@pytest.mark.parametrize("package,version", [("context-engineering", "2.6.0"), ("writing-check", "1.0.0")])
def test_release_rejects_wrong_tag_ref_or_version(package, version):
    tag = f"{package}-v{version}"
    wrong = "writing-check" if package == "context-engineering" else "context-engineering"
    for ref, candidate in [
        (f"refs/tags/{tag}", f"{wrong}-v{version}"),
        ("refs/heads/main", tag),
        (f"refs/tags/{tag}", f"{package}-v999.0.0"),
        (f"refs/tags/{tag}", f"{tag}-extra"),
    ]:
        with pytest.raises(ValueError):
            publish.release_identity(package, ref, candidate)


@pytest.mark.parametrize("package", ["context-engineering", "writing-check"])
def test_publish_workflows_are_scoped_to_release_or_guarded_recovery(package):
    workflow = (ROOT / ".github/workflows" / f"publish-{package}.yml").read_text()
    assert "  release:\n    types: [published]" in workflow
    assert "push:" not in workflow and "pull_request:" not in workflow
    assert "environment:" not in workflow
    assert f"check_publish.py {package}" in workflow
    assert f"uv build packages/{package} --out-dir dist" in workflow
    assert "id-token: write" in workflow and "contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33" in workflow
    build, publish_job = workflow.split("  publish:\n", 1)
    assert "id-token: write" not in build
    assert "id-token: write" in publish_job and "actions/checkout@" not in publish_job
    assert "needs: build" in publish_job
    assert "actions/upload-artifact@" in build and "actions/download-artifact@" in publish_job
    assert "EXPECTED_DIGEST" in publish_job
    download = publish_job.split("      - uses: actions/download-artifact@", 1)[1].split("      - name:", 1)[0]
    assert "artifact-ids: ${{ needs.build.outputs.artifact_id }}" in download
    assert "path: dist/\n          merge-multiple: true" in download
    assert 'test "$(find dist -mindepth 1 -type d | wc -l)" -eq 0' in publish_job
    assert "python scripts/fast_check.py" in workflow
    checkout = build.split("      - uses: actions/checkout@", 1)[1].split("      - uses:", 1)[0]
    if package == "context-engineering":
        assert "workflow_dispatch:" in workflow
        assert "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.tag || github.sha }}" in checkout
        assert 'test "$(git rev-parse --verify "refs/tags/$RELEASE_TAG^{commit}")" = "$EXPECTED_SHA"' in build
        assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"' in build
        assert 'release["target_commitish"] != os.environ["EXPECTED_SHA"]' in build
    else:
        assert "workflow_dispatch:" not in workflow
        assert "ref: ${{ github.sha }}" in checkout
        assert 'test "$(git rev-parse --verify "refs/tags/$RELEASE_TAG^{commit}")" = "$GITHUB_SHA"' in build
    assert "fetch-depth: 0" in checkout
    assert "persist-credentials: false" in checkout
    assert "git fetch" not in build


@pytest.mark.parametrize("package,version", [("context-engineering", "2.6.0"), ("writing-check", "1.0.0")])
def test_release_rejects_metadata_tampering(package, version, tmp_path):
    name, module = publish.PACKAGES[package]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages" / package), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    publish.check_artifacts(dist, name, module, version)
    wheel = next(dist.glob("*.whl"))
    original = wheel.read_bytes()
    info = f"{name.replace('-', '_')}-{version}.dist-info/"
    for suffix, replacement, error in [
        ("METADATA", b"Requires-Dist: tampered-package==1\n", "dependencies"),
        ("entry_points.txt", b"[console_scripts]\nmissing-command = missing:main\n", "entry points"),
    ]:
        altered = tmp_path / "altered.whl"
        with zipfile.ZipFile(wheel) as source, zipfile.ZipFile(altered, "w") as target:
            for member in source.infolist():
                data = source.read(member)
                if member.filename == info + suffix:
                    data = replacement + data if suffix == "METADATA" else replacement
                target.writestr(member, data)
        shutil.copyfile(altered, wheel)
        with pytest.raises(ValueError, match=error):
            publish.check_artifacts(dist, name, module, version)
        wheel.write_bytes(original)


@pytest.mark.parametrize("wheel", [True, False])
def test_writing_check_rejects_tampered_metadata_description(wheel, tmp_path):
    name, module = publish.PACKAGES["writing-check"]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/writing-check"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    replacement = b"unreviewed release description\n"
    if wheel:
        artifact = next(dist.glob("*.whl"))
        altered = tmp_path / "altered.whl"
        with zipfile.ZipFile(artifact) as source, zipfile.ZipFile(altered, "w") as target:
            for member in source.infolist():
                data = source.read(member)
                if member.filename.endswith(".dist-info/METADATA"):
                    data = data.split(b"\n\n", 1)[0] + b"\n\n" + replacement
                target.writestr(member, data)
    else:
        artifact = next(dist.glob("*.tar.gz"))
        altered = tmp_path / "altered.tar.gz"
        with tarfile.open(altered, "w:gz") as target:
            with tarfile.open(artifact, "r:gz") as source:
                for member in source:
                    if member.name.endswith("/PKG-INFO"):
                        data = source.extractfile(member).read().split(b"\n\n", 1)[0] + b"\n\n" + replacement
                        member.size = len(data)
                        target.addfile(member, io.BytesIO(data))
                    else:
                        target.addfile(member, source.extractfile(member) if member.isfile() else None)
    shutil.copyfile(altered, artifact)
    with pytest.raises(ValueError, match="archive description differs from source README"):
        publish.check_artifacts(dist, name, module, "1.0.0")


@pytest.mark.parametrize("package,version", [("context-engineering", "2.6.0"), ("writing-check", "1.0.0")])
def test_release_rejects_unsafe_sdist_directory(package, version, tmp_path):
    name, module = publish.PACKAGES[package]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages" / package), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    sdist = next(dist.glob("*.tar.gz"))
    with tarfile.open(tmp_path / "altered.tar.gz", "w:gz") as target:
        with tarfile.open(sdist, "r:gz") as source:
            for member in source:
                target.addfile(member, source.extractfile(member) if member.isfile() else None)
        directory = tarfile.TarInfo("../private")
        directory.type = tarfile.DIRTYPE
        target.addfile(directory)
    shutil.copyfile(tmp_path / "altered.tar.gz", sdist)
    with pytest.raises(ValueError, match="unsafe archive path"):
        publish.check_artifacts(dist, name, module, version)


@pytest.mark.parametrize("wheel", [True, False])
def test_writing_check_archives_require_exact_google_notice(wheel, tmp_path):
    name, module, version = "writing-check-cli", "writing_check", "1.0.0"
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/writing-check"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    if wheel:
        with zipfile.ZipFile(next(dist.glob("*.whl"))) as archive:
            members = {item.filename: archive.read(item) for item in archive.infolist()}
        notice = "writing_check/vale/vendor/Google-NOTICE.md"
    else:
        with tarfile.open(next(dist.glob("*.tar.gz")), "r:gz") as archive:
            members = {item.name: archive.extractfile(item).read() for item in archive if item.isfile()}
        notice = "writing_check_cli-1.0.0/src/writing_check/vale/vendor/Google-NOTICE.md"
    source = ROOT / "packages/writing-check/src/writing_check/vale/vendor/Google-NOTICE.md"
    assert members[notice] == source.read_bytes()
    text = source.read_text()
    for required in (
        "vale-cli/Google/tree/v0.7.1",
        "Google-LICENSE",
        "developers.google.com/style",
        "creativecommons.org/licenses/by/4.0/",
        "not maintained or endorsed by Google",
        "normalizes rule severity levels to suggestions",
    ):
        assert required in text
    publish.check_members(members, name, module, version, wheel)
    del members[notice]
    with pytest.raises(ValueError, match="required archive members missing"):
        publish.check_members(members, name, module, version, wheel)
    members[notice] = source.read_bytes().replace(b"not maintained or endorsed", b"endorsed")
    with pytest.raises(ValueError, match="package payload differs from source"):
        publish.check_members(members, name, module, version, wheel)


def test_writing_check_sdist_rejects_tampered_readme(tmp_path):
    name, module = publish.PACKAGES["writing-check"]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/writing-check"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    sdist = next(dist.glob("*.tar.gz"))
    with tarfile.open(tmp_path / "altered.tar.gz", "w:gz") as target:
        with tarfile.open(sdist, "r:gz") as source:
            for member in source:
                if member.name.endswith("/README.md"):
                    data = b"unreviewed release instructions\n"
                    member.size = len(data)
                    target.addfile(member, io.BytesIO(data))
                else:
                    target.addfile(member, source.extractfile(member) if member.isfile() else None)
    shutil.copyfile(tmp_path / "altered.tar.gz", sdist)
    with pytest.raises(ValueError, match="sdist README differs from source"):
        publish.check_artifacts(dist, name, module, "1.0.0")


def test_writing_check_sdist_requires_readme(tmp_path):
    name, module = publish.PACKAGES["writing-check"]
    dist = tmp_path / "dist"
    result = subprocess.run(["uv", "build", str(ROOT / "packages/writing-check"), "--out-dir", str(dist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    (dist / ".gitignore").unlink()
    sdist = next(dist.glob("*.tar.gz"))
    with tarfile.open(tmp_path / "altered.tar.gz", "w:gz") as target:
        with tarfile.open(sdist, "r:gz") as source:
            for member in source:
                if member.name.endswith("/README.md"):
                    continue
                target.addfile(member, source.extractfile(member) if member.isfile() else None)
    shutil.copyfile(tmp_path / "altered.tar.gz", sdist)
    with pytest.raises(ValueError, match="required archive members missing"):
        publish.check_artifacts(dist, name, module, "1.0.0")
