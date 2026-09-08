import hashlib, json, os, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).parents[1]
CATALOG = {"context-agents-md", "context-improve", "context-contracts", "context-backfill", "context-docs", "context-review", "repository-context-refresh", "session-capture", "writing-core", "writing-check", "anti-llm-writer", "user-facing-response", "readme-improver", "pr-description"}
CONTEXT_COMMANDS = {"tier", "antipatterns", "depth", "staleness", "sessions", "cross-cutting", "frontmatter", "references", "skills", "contracts", "review", "check", "backfill"}


def run(*args, cwd=ROOT, env=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(ROOT / "packages/context-engineering"), **(env or {})})


def context(*args, cwd=ROOT):
    return run(sys.executable, "-m", "context_engineering", *args, "--json", cwd=cwd)


def writing(*args, env=None):
    return run(sys.executable, "packages/writing-check/scripts/writing_check.py", *args, env=env)


def git_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    run("git", "init", str(repo)); run("git", "-C", str(repo), "config", "user.email", "test@example.invalid"); run("git", "-C", str(repo), "config", "user.name", "Test")
    (repo / "AGENTS.md").write_text("# Guide\n\nUse tests.\n")
    (repo / "docs").mkdir(); (repo / "docs" / "index.md").write_text("# Docs\n")
    (repo / "SPEC.md").write_text("# Specification\n")
    (repo / "module").mkdir(); (repo / "module" / "one.py").write_text("import os\n")
    (repo / "other").mkdir(); (repo / "other" / "two.py").write_text("import module.one\n")
    run("git", "-C", str(repo), "add", "."); run("git", "-C", str(repo), "commit", "-m", "base")
    return repo


def test_catalog_contracts_have_distinctive_workflow_guards():
    skills = {p.parent.name: p.read_text() for p in ROOT.glob("skills/*/*/SKILL.md")}
    assert set(skills) == CATALOG
    expected = {"context-agents-md": "DO/NOT/BECAUSE", "context-improve": "two modes", "context-contracts": "Analyze", "context-backfill": "cutoff", "context-docs": "Analyze", "context-review": "read-only", "repository-context-refresh": "Audit", "session-capture": "subsequent user turn", "writing-core": "Preserve", "writing-check": "exact", "anti-llm-writer": "LLM-shaped", "user-facing-response": "preservation ledger", "readme-improver": "reader journey", "pr-description": "base and head"}
    for name, phrase in expected.items(): assert phrase.lower() in skills[name].lower()


def test_capture_and_context_contracts_preserve_portable_current_behavior():
    capture = (ROOT / "skills/context/session-capture/SKILL.md").read_text()
    repo_context = (ROOT / "skills/context/session-capture/references/repo-context.md").read_text()
    agents = (ROOT / "skills/context/context-agents-md/SKILL.md").read_text()
    generated_spec = (ROOT / "skills/context/context-agents-md/resources/generated-doc-spec.md").read_text()
    docs = (ROOT / "skills/context/context-docs/SKILL.md").read_text()

    assert "Treat each number as one complete decision bundle" in capture
    assert "Targets: <primary path>; <required companion paths>" in capture
    assert "selectable suffix" not in capture
    assert "include it in the same numbered decision bundle" in repo_context
    assert "compulsory mid-task capture paragraph" in agents
    assert "<self-doc requirement paragraph>" not in agents
    assert "### 2. Capture authority" in generated_spec
    assert "Self-Documentation Requirement" not in generated_spec
    assert "Portable catalog release: `safurrier-skills`" in docs


def test_metadata_provenance_privacy_and_copied_artifact_validate():
    assert run(sys.executable, "scripts/validate.py").returncode == 0


def test_shipped_skills_have_no_experimental_maturity_label():
    for skill in ROOT.glob("skills/*/*/SKILL.md"):
        assert "experimental" not in skill.read_text().lower(), skill


def test_context_docs_verifier_available_unavailable_and_readonly(tmp_path):
    target = git_repo(tmp_path)
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file() and ".git" not in p.parts}
    verifier = ROOT / "skills/context/context-docs/scripts/docs_verify.py"
    available = run(sys.executable, str(verifier), str(target))
    data = json.loads(available.stdout)
    assert available.returncode == 0 and data["context_cli"] == "available" and data["findings"] == []
    assert {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file() and ".git" not in p.parts} == before

    copied = tmp_path / "context-docs"; shutil.copytree(ROOT / "skills/context/context-docs", copied)
    unavailable = run(sys.executable, str(copied / "scripts/docs_verify.py"), str(target))
    data = json.loads(unavailable.stdout)
    assert unavailable.returncode == 0 and data["context_cli"] == "unavailable" and data["findings"] == []
    assert {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file() and ".git" not in p.parts} == before


def test_context_markdown_local_paths_and_skill_commands_resolve():
    markdown = list((ROOT / "skills/context").rglob("*.md"))
    for path in markdown:
        text = path.read_text()
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
            if "://" not in target:
                assert (path.parent / target).exists(), (path, target)
        for target in re.findall(r"`((?:references|resources|scripts)/[^`\s]+)`", text):
            assert (path.parent / target).exists(), (path, target)
        skill_root = next((parent for parent in (path.parent, *path.parents) if (parent / "SKILL.md").exists()), None)
        for target in re.findall(r"<skill-dir>/(scripts/[^\s>`]+)", text):
            assert skill_root is not None and (skill_root / target).exists(), (path, target)


def test_context_commands_run_readonly_on_meaningful_fixture(tmp_path):
    repo = git_repo(tmp_path); before = {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts}
    base = run("git", "-C", str(repo), "rev-parse", "HEAD").stdout.strip(); (repo / "note.md").write_text("# change\n")
    invocations = [
        ("tier", str(repo / "module")), ("antipatterns", str(repo)), ("depth", str(repo / "AGENTS.md")), ("staleness", str(repo / "AGENTS.md")), ("sessions", str(repo)), ("cross-cutting", str(repo / "module"), str(repo / "other")), ("frontmatter", str(repo)), ("references", str(repo)), ("skills", str(ROOT / "skills"), "--all"), ("contracts", str(repo)), ("review", str(repo), "--base", base, "--head", "HEAD"), ("check", str(repo), "--base", base, "--head", "HEAD"), ("backfill", str(repo)),
    ]
    for invocation in invocations:
        result = context(*invocation)
        assert result.returncode in (0, 1), (invocation, result.stdout, result.stderr)
        assert result.stdout.strip().startswith("{")
    for path, content in before.items(): assert (repo / path).read_bytes() == content
    assert (repo / "note.md").read_text() == "# change\n"


def test_context_markdown_commands_are_portable_and_resolve_in_copy(tmp_path):
    artifact = tmp_path / "artifact"; shutil.copytree(ROOT, artifact, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "site"))
    text = "\n".join(p.read_text() for p in artifact.rglob("*.md"))
    assert "uv run --project" not in text
    commands = set(re.findall(r"python3 -m context_engineering ([a-z-]+)", text))
    assert commands <= CONTEXT_COMMANDS and commands
    for command in commands:
        assert subprocess.run([sys.executable, "-m", "context_engineering", command, "--help"], env={**os.environ, "PYTHONPATH": str(artifact / "packages/context-engineering")}, text=True, capture_output=True).returncode == 0


def test_writing_profiles_policy_identity_and_unavailable_vale(tmp_path):
    sample = tmp_path / "sample.md"; sample.write_text("This is a short candidate with no prohibited wording.")
    profiles = json.loads((ROOT / "packages/writing-check/vale/profiles.json").read_text())["profiles"]
    for profile, policy in profiles.items():
        result = writing("--profile", profile, "--json", str(sample), env={"PATH": "/nonexistent"})
        data = json.loads(result.stdout)
        assert result.returncode == 3 and data["status"] == "unavailable"
        assert data["source"]["text"] == sample.read_text() and data["source"]["sha256"] == hashlib.sha256(sample.read_bytes()).hexdigest()
        assert data["policy"]["name"] == policy["policy"] and len(data["policy"]["sha256"]) == 64
    bad = writing("--profile", "bad", "--json", str(sample)); assert bad.returncode == 2 and json.loads(bad.stdout)["error"]["code"] == "unknown_profile"
    broken = tmp_path / "bad.md"; broken.write_bytes(b"\xff"); assert writing("--profile", "readme", "--json", str(broken)).returncode == 2


def test_writing_vale_normalization_and_composition_limit(tmp_path):
    sample = tmp_path / "candidate.md"; sample.write_text("A short candidate.")
    fake = tmp_path / "bin"; fake.mkdir(); vale = fake / "vale"; vale.write_text("#!/bin/sh\nprintf '{\"candidate.md\":[{\"Check\":\"Portable.Specificity\",\"Message\":\"Be specific\",\"Line\":2,\"Span\":[1,4]}]}'\n"); vale.chmod(0o755)
    result = writing("--profile", "pr-description", "--json", str(sample), env={"PATH": str(fake) + os.pathsep + os.environ["PATH"]}); data = json.loads(result.stdout)
    assert result.returncode == 1 and data["alerts"][0]["severity"] == "suggestion" and data["vale"]["status"] == "ran"
    table = tmp_path / "table.md"; table.write_text("| Item | Detail |\n| --- | --- |\n" + "\n".join("| alpha beta gamma delta epsilon | zeta eta theta iota kappa |" for _ in range(20)))
    result = writing("--profile", "readme", "--json", str(table), env={"PATH": "/nonexistent"}); assert json.loads(result.stdout)["readability"]["status"] == "composition_limited"


def test_selected_skill_copy_closure_and_plugin_metadata(tmp_path):
    out = tmp_path / "writing-check"; shutil.copytree(ROOT / "skills/writing/writing-check", out)
    candidate = tmp_path / "candidate.md"; candidate.write_text("A candidate.")
    result = run(sys.executable, str(out / "scripts/writing_check.py"), "--profile", "commit", "--json", str(candidate), env={"PATH": "/nonexistent"})
    assert result.returncode == 3 and json.loads(result.stdout)["status"] == "unavailable"
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text()); assert plugin["skills"] == "../skills"


def test_routes_resolve_or_describe_external_fallback():
    text = "\n".join(p.read_text() for p in ROOT.glob("skills/*/*/SKILL.md"))
    names = set(re.findall(r"`([a-z][a-z0-9-]+)`", text))
    missing = names - CATALOG - {"Git", "Vale", "UTF", "JSON", "Audit", "Apply", "Draft", "Improve", "Analyze", "Init", "Update", "Consolidate", "Bootstrap", "Validate", "AGENTS", "SPEC", "ADR", "README", "FRE", "FK"}
    assert not {"alex-writing-editor", "commit-message", "github-open-pr", "writing-voice-check"} & missing
