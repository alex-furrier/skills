# PyPI release preparation

These are **candidate** workflows, not evidence that either project exists on PyPI. Keep using the source-checkout installation instructions until publication is independently verified. The distributions are independently versioned:

| Distribution | Project directory | Release tag | Workflow | GitHub environment |
| --- | --- | --- | --- | --- |
| `safurrier-context-engineering` | `packages/context-engineering` | `context-engineering-vX.Y.Z` | publish-context-engineering.yml | `pypi-context-engineering` |
| `safurrier-writing-check` | `packages/writing-check` | `writing-check-vX.Y.Z` | publish-writing-check.yml | `pypi-writing-check` |

Only publishing a GitHub Release on an exact matching tag routes to the corresponding job; push, PR, and draft releases do not deploy. The tag must identify the same version as that package's `pyproject.toml`. The workflow checks the release identity, tag target, full repository fast check, and built wheel/sdist at the release event commit in a job without OIDC. A separate protected-environment upload job receives only the validated artifacts and checks their digest before the trusted-publisher upload. Each release uploads exactly one distribution. Do not use an unreviewed tag, release, or artifact.

Before enabling a first release, repository and PyPI owners must:

1. Confirm ownership/availability and existing versions of **each** exact PyPI project name, release authority, and permitted first version; never overwrite an existing version. Confirm the packaged portable source and the vendored Google Vale policy/license/provenance are cleared for public redistribution, including no private corpus, credentials, or machine-specific material.
2. Protect the release tag prefixes (`context-engineering-v*` and `writing-check-v*`) against unauthorized creation, updates, and deletion, and create and protect the two GitHub environments above (limit release approval to authorized maintainers). In each PyPI project configure an OIDC trusted publisher for owner `safurrier`, repository `skills`, its exact workflow filename above, and corresponding environment. If a project does not yet exist, follow PyPI's pending-publisher bootstrap procedure with that exact tuple. Do not add a PyPI API token or repository secret.
3. Review the source at the release tag, its changelog and metadata, run `python scripts/fast_check.py`, and build each intended package in an empty output directory. Run `python scripts/check_publish.py <package-key> refs/tags/<tag> <tag> --dist <dist-directory>`; inspect the wheel/sdist, notices and provenance. For Writing Check, verify the pinned `vale` dependency's first-use executable download behavior and network/prerequisite expectations in a clean environment. CI cannot establish private-source rights or PyPI namespace ownership.
4. Only after review and approval, create the corresponding tag and publish its GitHub Release. The release workflow must be present on the default branch. Observe the workflow, verify the uploaded project/version and clean installation before changing installation guidance. No publication is part of this preparation branch.
