# PyPI publishing

The independently versioned distributions are published:

- [Writing Check CLI 1.0.1](https://pypi.org/project/writing-check-cli/1.0.1/): [release run](https://github.com/alex-furrier/skills/actions/runs/41083408841), [writing-check-v1.0.1](https://github.com/alex-furrier/skills/releases/tag/writing-check-v1.0.1), source commit `378c2355076a38ca16399a055ed87249e1c79dc9`.
- [Context Engineering CLI 2.6.1](https://pypi.org/project/context-engineering-cli/2.6.1/): [release run](https://github.com/alex-furrier/skills/actions/runs/36173696116), [context-engineering-v2.6.1](https://github.com/alex-furrier/skills/releases/tag/context-engineering-v2.6.1), source commit `fda3af779a399f7b3b5f586e7dcf119d2be3638c`.
- [Code Health Review CLI 0.2.0](https://pypi.org/project/code-health-review-cli/0.2.0/): [release run](https://github.com/alex-furrier/skills/actions/runs/43335468277), [code-health-v0.2.0](https://github.com/alex-furrier/skills/releases/tag/code-health-v0.2.0), source commit `41ac7f2dca2269aba11bb3375051e64cfb27ed93`.

Fresh Python 3.11 registry installs passed. Writing Check 1.0.1 produced the expected real Vale warning and clean control results, with exact source identities. Context Engineering 2.6.1 passed synthetic sessions checks. Code Health Review 0.2.0 passed a clean `uv tool install code-health-review-cli==0.2.0`. See [installation](installation.md) for public installs.

The first Writing Check 1.0.0 publication used [this release run](https://github.com/alex-furrier/skills/actions/runs/36072533222). The original Context 2.6.0 publication used a [recovery run](https://github.com/alex-furrier/skills/actions/runs/36072208510). The first-release tags and publisher configuration remain:

| Distribution | Project directory | First release tag | PyPI trusted publisher workflow filename | PyPI environment field |
| --- | --- | --- | --- | --- |
| `context-engineering-cli` | `packages/context-engineering` | context-engineering-v2.6.0 | publish-context-engineering.yml | Leave blank |
| `writing-check-cli` | `packages/writing-check` | writing-check-v1.0.0 | publish-writing-check.yml | Leave blank |
| `code-health-review-cli` | `packages/code-health` | code-health-v0.2.0 | publish-code-health.yml | Leave blank |

## Writing Check 1.0.1 correction

The patch corrects Vale stdin forwarding and adds real-runtime warning/clean
controls for file, stdin, and sweep inputs. In 1.0.0, the forwarded hyphen can
produce empty alerts without checking the candidate. Stored source identity and
readability do not establish that Vale linted it. Rerun needed lint checks with
1.0.1 on the exact candidate; existing semantic judgments remain separate.

The published 1.0.1 wheel and source archive passed digest and payload checks
against the reviewed source. Installation guidance now pins that release.
Context Engineering needs no package release for this fix. An installed-tool
upgrade remains a deliberate action; updating skill instructions alone does not
replace the Python CLI.

## Release controls

Publishing a GitHub Release on an exact matching tag triggers the corresponding job; push, PR, and draft releases do not publish. The one manual recovery dispatch for the existing Context release checks its published tag and approved commit before running the same build and upload gates.

The tag must identify the same version as that package's `pyproject.toml`, and the release must target the reviewed full commit SHA (not a branch name). The workflow checks release identity, tag target, full repository fast check, and built wheel/sdist in a job without OIDC.

A separate minimal-permission OIDC upload job verifies the artifact digest before the trusted-publisher upload. Each release uploads exactly one distribution. Do not use an unreviewed tag, release, or artifact.

For subsequent releases, retain these controls from the first-release preparation:

1. Confirm ownership/availability and existing versions of **each** exact PyPI project name, release authority, and permitted first version; never overwrite an existing version.

   Confirm the packaged portable source and the vendored Google Vale policy/license/provenance are cleared for public redistribution, including no private corpus, credentials, or machine-specific material.
2. The first-release path was configured with **no enforced environment reviewer gate or release-tag protection rules**: anyone with sufficient repository release/tag or workflow authority could trigger publication. Verify the current controls before a subsequent release.

   Before any tag or GitHub Release, the account owner must manually approve the proposed source commit and tag target, prior CI results, locally built artifacts, and public redistribution. Review release CI and its artifacts after the workflow runs; there is no pause for approval before its upload. Manual review is a procedure, not a GitHub-enforced safeguard.

   The existing projects use the trusted-publisher identity shown above: GitHub owner `alex-furrier`, repository `skills`, exact workflow filename, and no environment. Verify that account-side configuration before changing publisher settings; do not add a PyPI API token or repository secret.
3. Review the source at the release tag, its changelog and metadata, run `python scripts/fast_check.py`, and build each intended package in an empty output directory. Run `python scripts/check_publish.py <package-key> refs/tags/<tag> <tag> --dist <dist-directory>`; inspect the wheel/sdist, notices and provenance. For Writing Check, verify the pinned `vale` dependency's first-use executable download behavior and network/prerequisite expectations in a clean environment. CI cannot establish private-source rights or PyPI namespace ownership.
4. Only after review and approval, create the corresponding tag and publish its GitHub Release. The release workflow must be present on the default branch. Observe the workflow, verify the uploaded project/version and clean installation before changing installation guidance.

## Add a new package

Code Health Review CLI 0.2.0 shipped with this sequence. It covers the per-package setup. The [release controls](#release-controls) above still apply.

1. Confirm that the exact PyPI name is free (`https://pypi.org/pypi/<name>/json` returns 404) and choose the first version.
2. Copy `.github/workflows/publish-code-health.yml` to `.github/workflows/publish-<package>.yml`. Change the workflow name, tag prefix, package-key arguments to `check_publish.py`, package paths, and artifact name; preserve the remaining release controls. Don't copy the Context Engineering workflow, whose recovery dispatch is specific to that package. Add the package to `PACKAGES` and the README checks in `scripts/check_publish.py`, and to the parametrized cases in `tests/test_publish.py`. Include a version-mismatch case whose ref and tag agree with each other but not with `pyproject.toml`; otherwise the ref/tag check fails first and masks the version check.
3. Write the package README as release text. `check_publish.py` requires the PyPI long description to match it byte for byte, so leave out release status such as "not published yet". Link the repository explicitly, because `pyproject.toml` has no project URLs.
4. Before the first release, the account owner adds a pending trusted publisher at <https://pypi.org/manage/account/publishing/> on the GitHub tab: the PyPI project name, owner `alex-furrier`, repository `skills`, the workflow filename, and a blank environment, since the publish job has none. A pending publisher creates nothing on PyPI by itself.
5. Merge, then publish a GitHub Release tagged `<package>-v<version>` that targets the full merge commit SHA, not `main`. Pass `--latest=false` so a package release doesn't take "Latest" from the other packages:

   ```bash
   gh release create <package>-v<version> --target <full-merge-sha> --latest=false
   ```

6. Watch the publish run through the build job and the OIDC upload job. Then install the release in a clean, isolated environment with `uv tool install <name>==<version>` and run `<command> --version`.
7. In a follow-up docs PR, pin the install in `docs/installation.md` and `README.md`, add the release record at the top of this file and a row to the publisher table, and add a `CHANGELOG.md` entry. Leave historical changelog entries unchanged.
