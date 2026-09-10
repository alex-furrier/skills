import hashlib
import json
import os
import pathlib
import re
import runpy
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parents[1]
PLUGIN = ROOT / "plugins/context-engineering"
CLI = PLUGIN / "cli"
CONTEXT = {"context-agents-md", "context-improve", "context-contracts", "context-backfill", "context-docs", "context-review", "repository-context-refresh", "session-capture"}
WRITING = {"writing-core", "writing-check", "anti-llm-writer", "user-facing-response", "readme-improver", "pr-description"}


def run(*args, cwd=ROOT, env=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, env={**os.environ, **(env or {})})


def context(*args, project=CLI, cwd=ROOT):
    return run("uv", "run", "--no-config", "--locked", "--no-dev", "--project", str(project), "context-engineering", *args, cwd=cwd)


def git_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    for args in (("init",), ("config", "user.email", "test@example.invalid"), ("config", "user.name", "Test")):
        run("git", "-C", str(repo), *args)
    (repo / "AGENTS.md").write_text("# Guide\n\nUse tests.\n")
    (repo / "docs").mkdir(); (repo / "docs/index.md").write_text("# Docs\n")
    (repo / "module").mkdir(); (repo / "module/one.py").write_text("import os\n")
    run("git", "-C", str(repo), "add", "."); run("git", "-C", str(repo), "commit", "-m", "base")
    return repo


def files(root):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts}


def test_atomic_context_plugin_metadata_and_inventory():
    manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert manifest["skills"] == "./skills"
    assert marketplace["plugins"] == [{"name": "context-engineering", "source": "./plugins/context-engineering", "description": "Portable deterministic Context engineering skills"}]
    assert not (ROOT / ".claude-plugin.json").exists()
    assert {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")} == CONTEXT
    assert not (ROOT / "skills/context").exists()


def test_context_installation_docs_use_claude_marketplace_commands():
    text = "\n".join((ROOT / path).read_text() for path in ("README.md", "docs/installation.md"))
    assert "/plugin marketplace add safurrier/skills" in text
    assert "/plugin install context-engineering@safurrier-skills" in text
    assert "context-engineering --help" in text
    assert "npx skills add safurrier/skills --skill writing-check" in text


def test_context_plugin_copy_is_relocatable_readonly(tmp_path):
    plugin = tmp_path / "arbitrary" / "context-engineering"; plugin.parent.mkdir(); shutil.copytree(PLUGIN, plugin)
    target = git_repo(tmp_path)
    before = files(target)
    assert context("--help", project=plugin / "cli").returncode == 0
    result = context("references", str(target), "--json", project=plugin / "cli")
    assert result.returncode == 0 and result.stdout.startswith("{")
    assert files(target) == before


def test_context_plugin_copy_retains_scoped_license_and_provenance(tmp_path):
    plugin = tmp_path / "arbitrary" / "context-engineering"; plugin.parent.mkdir(); shutil.copytree(PLUGIN, plugin)
    inventory = json.loads((plugin / "provenance.json").read_text())
    assert "complete legal and provenance contract" in inventory["decision"]
    assert (plugin / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    result = run(sys.executable, "scripts/validate.py", "--plugin", str(plugin))
    assert result.returncode == 0 and result.stdout == "plugin validation passed\n"


def test_context_plugin_copy_rejects_live_and_broken_symlinks(tmp_path):
    plugin = tmp_path / "context-engineering"
    shutil.copytree(PLUGIN, plugin)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside the plugin")
    (plugin / "skills/live-link").symlink_to(outside)
    (plugin / "skills/broken-link").symlink_to(tmp_path / "missing")

    result = run(sys.executable, "scripts/validate.py", "--plugin", str(plugin))
    assert result.returncode != 0
    assert "Context plugin must not contain symlink: skills/live-link" in result.stdout
    assert "Context plugin must not contain symlink: skills/broken-link" in result.stdout


def test_context_plugin_ignores_generated_environment_symlinks(tmp_path):
    plugin = tmp_path / "context-engineering"
    shutil.copytree(PLUGIN, plugin, ignore=shutil.ignore_patterns(".venv"))
    environment = plugin / "cli/.venv/bin"
    environment.mkdir(parents=True)
    (environment / "python").symlink_to(tmp_path / "python")

    result = run(sys.executable, "scripts/validate.py", "--plugin", str(plugin))
    assert result.returncode == 0 and result.stdout == "plugin validation passed\n"


def test_context_skill_only_copy_reports_unavailable(tmp_path):
    target = git_repo(tmp_path)
    copied = tmp_path / "context-docs"; shutil.copytree(PLUGIN / "skills/context-docs", copied)
    result = run(sys.executable, str(copied / "scripts/docs_verify.py"), str(target))
    assert result.returncode == 3
    assert json.loads(result.stdout)["context_cli"] == "unavailable"


def test_context_docs_verifier_works_inside_complete_plugin(tmp_path):
    plugin = tmp_path / "plugin"; shutil.copytree(PLUGIN, plugin)
    target = git_repo(tmp_path)
    result = run(sys.executable, str(plugin / "skills/context-docs/scripts/docs_verify.py"), str(target))
    assert result.returncode == 0 and json.loads(result.stdout)["context_cli"] == "available"


def test_context_skill_commands_use_plugin_local_locked_cli():
    text = "\n".join(path.read_text() for path in (PLUGIN / "skills").rglob("*.md"))
    assert "packages/context-engineering" not in text
    assert "<context-plugin-root>/cli" in text
    assert "uv run --no-config --locked --no-dev --project" in text


def test_writing_check_is_the_single_self_contained_policy_tree(tmp_path):
    skill = ROOT / "skills/writing/writing-check"
    assert not (ROOT / "packages/writing-check").exists()
    assert len(list(ROOT.rglob("upstream-lock.json"))) == 1
    copied = tmp_path / "writing-check"; shutil.copytree(skill, copied)
    sample = tmp_path / "sample.md"; sample.write_text("A candidate.")
    unavailable = run(sys.executable, str(copied / "scripts/writing_check.py"), "--profile", "commit", "--json", str(sample), env={"PATH": "/nonexistent"})
    assert unavailable.returncode == 3 and json.loads(unavailable.stdout)["status"] == "unavailable"
    lock = json.loads((copied / "vale/upstream-lock.json").read_text())
    profiles = json.loads((copied / "vale/profiles.json").read_text())
    assert (copied / "vale/vendor/Google-LICENSE").is_file() and len(profiles["rules"]) == 34
    for data in profiles["rules"].values(): assert hashlib.sha256((copied / "vale" / data["path"]).read_bytes()).hexdigest() == data["sha256"]
    assert hashlib.sha256((copied / "vale" / lock["upstream"]["license_file"]).read_bytes()).hexdigest() == lock["upstream"]["license_sha256"]


def test_writing_check_fake_vale_preserves_advisory_behavior(tmp_path):
    sample = tmp_path / "sample.md"; sample.write_text("A candidate.")
    copied = tmp_path / "writing-check"; shutil.copytree(ROOT / "skills/writing/writing-check", copied)
    fake = tmp_path / "bin"; fake.mkdir(); vale = fake / "vale"
    vale.write_text("#!/bin/sh\nprintf '{\"candidate.md\":[{\"Check\":\"GoogleDocs.AMPM\",\"Message\":\"Use a.m.\",\"Line\":2,\"Span\":[1,4]}]}'\n")
    vale.chmod(0o755)
    result = run(sys.executable, str(copied / "scripts/writing_check.py"), "--profile", "commit", "--json", str(sample), env={"PATH": str(fake)})
    data = json.loads(result.stdout)
    assert result.returncode == 1 and data["alerts"][0]["severity"] == "suggestion" and data["vale"]["status"] == "ran"


def test_validation_and_documented_install_boundaries():
    assert run(sys.executable, "scripts/validate.py").returncode == 0
    text = "\n".join((ROOT / path).read_text() for path in ("README.md", "docs/installation.md", "docs/validation.md"))
    assert "npx skills add safurrier/skills --skill writing-check" in text
    assert "skills.sh" in text
    assert "<context-plugin-root>/cli" in text
    assert "packages/writing-check" not in text and "packages/context-engineering" not in text


def test_all_skills_have_valid_metadata_and_links_resolve():
    skills = list((PLUGIN / "skills").glob("*/SKILL.md")) + list((ROOT / "skills/writing").glob("*/SKILL.md"))
    assert {path.parent.name for path in skills} == CONTEXT | WRITING
    names = []
    for skill in skills:
        match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---", skill.read_text(), re.S)
        assert match and match.group(1) == skill.parent.name and match.group(2).strip()
        names.append(match.group(1))
    assert len(names) == len(set(names))
    for path in ROOT.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts): continue
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text()):
            if "://" not in target: assert (path.parent / target).exists(), (path, target)


def test_skill_direct_resource_links_have_one_level_closure():
    skills = list((PLUGIN / "skills").glob("*/SKILL.md")) + list((ROOT / "skills/writing").glob("*/SKILL.md"))
    for skill in skills:
        direct = [skill.parent / target for target in re.findall(r"\[[^]]+\]\((references/[^)#]+|resources/[^)#]+)", skill.read_text())]
        for resource in direct:
            assert resource.is_file(), (skill, resource)
            for target in re.findall(r"\[[^]]+\]\(([^)#]+)", resource.read_text()):
                if "://" not in target:
                    assert (resource.parent / target).exists(), (resource, target)


def test_context_command_inventory_and_mutation_boundaries_are_explicit():
    help_result = context("--help")
    assert help_result.returncode == 0
    documented = {"antipatterns", "backfill", "check", "contracts", "cross-cutting", "depth", "frontmatter", "references", "review", "sessions", "skills", "staleness", "tier"}
    assert all(command in help_result.stdout for command in documented)
    for name in CONTEXT:
        text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
        assert "stop the requested deterministic-analysis workflow" in text
    assert "Audit-only runs do not edit files." in (PLUGIN / "skills/context-docs/SKILL.md").read_text()
    assert "Apply only after an explicit apply instruction" in (PLUGIN / "skills/context-review/SKILL.md").read_text()
    writing_check = (ROOT / "skills/writing/writing-check/SKILL.md").read_text()
    assert "Keep `writing_check.py` read-only." in writing_check
    assert "only after an explicit request" in writing_check
    exact_consumer = "Keep bytes exact only for a real exact-byte consumer"
    assert exact_consumer in writing_check
    assert "candidate supplied to this checker and its `source.sha256`" in writing_check
    assert exact_consumer in (ROOT / "skills/writing/writing-check/references/repository-sweep.md").read_text()
    assert exact_consumer.lower() in (PLUGIN / "skills/repository-context-refresh/SKILL.md").read_text()
    assert "safety, authentication, authority, factual, and contractual constraints" in writing_check


def test_context_review_uses_composed_check_evidence_once():
    review = (PLUGIN / "skills/context-review/SKILL.md").read_text()
    assert review.count("context-engineering check <target>") == 1
    assert "context-engineering review <target>" not in review
    assert "`advisory_routes`" in review
    assert "raw\n   changed paths, rename pairs, evidence" in review


def test_context_improve_delegates_owner_order_and_skipped_candidate_boundary():
    improve = (PLUGIN / "skills/context-improve/SKILL.md").read_text()
    owner = (PLUGIN / "skills/context-agents-md/SKILL.md").read_text()
    assert "Context-agents-md owns the generated AGENTS.md output shape" in improve
    assert "skipped-candidate triage and the\nproposal/apply boundary for `SKIPPED_FOR_REVIEW.md`" in improve
    assert "never create or modify any of those files here" in improve
    assert "Session-reflect" not in improve
    assert "do not count\npath segments inline" in improve
    assert "actually installed\nseparate multi-session provider" in improve
    assert "context-engineering sessions" not in improve
    assert "Session mining is default" not in improve
    assert "Session evidence is optional" in improve

    review = owner.index("### 4. Review and Apply AGENTS.md")
    apply = owner.index("until the user explicitly authorizes apply", review)
    validate = owner.index("### 5. Post-write Validate")
    assert review < apply < validate
    assert "no proposal validator is provided by this workflow" in owner
    assert "skipped-candidate triage proposal\nfor interactive review" in owner
    assert "Include any\nnon-empty skipped-file content in the interactive proposal" in owner
    assert "create it only as\npart of an explicitly authorized apply" in owner


def test_writing_check_profile_inventory_and_eval_manifest_validate():
    profiles = json.loads((ROOT / "skills/writing/writing-check/vale/profiles.json").read_text())["profiles"]
    assert {"technical-doc-explanatory", "technical-doc-reference"} <= set(profiles)
    sweep = (ROOT / "skills/writing/writing-check/references/repository-sweep.md").read_text()
    assert "technical-doc-explanatory" in sweep and "technical-doc-reference" in sweep
    result = run(sys.executable, "scripts/validate_evals.py")
    assert result.returncode == 0 and result.stdout == "eval manifest validation passed\n"


def test_eval_manifest_rejects_unknown_case_and_top_level_fields(tmp_path):
    validator = runpy.run_path(str(ROOT / "scripts/validate_evals.py"))["validate_manifest"]
    data = json.loads((ROOT / "evals/manifest.json").read_text())
    data["cases"][0]["must_observee"] = ["misspelled field"]
    manifest = tmp_path / "manifest.json"; manifest.write_text(json.dumps(data))
    assert "activation-stale-agents: unknown fields: must_observee" in validator(manifest)
    data = json.loads((ROOT / "evals/manifest.json").read_text())
    data["catalog_revison"] = "misspelled field"
    manifest.write_text(json.dumps(data))
    assert "eval manifest unknown fields: catalog_revison" in validator(manifest)


def test_eval_manifest_rejects_empty_protected_exact_text(tmp_path):
    validator = runpy.run_path(str(ROOT / "scripts/validate_evals.py"))["validate_manifest"]
    data = json.loads((ROOT / "evals/manifest.json").read_text())
    data["cases"][0]["protected_exact_text"] = [""]
    manifest = tmp_path / "manifest.json"; manifest.write_text(json.dumps(data))
    errors = validator(manifest)
    assert "activation-stale-agents: protected_exact_text must be a list of non-empty strings; an empty list is allowed" in errors
