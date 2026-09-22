# Contributing

Each contribution must identify its source or be independently authored, update `provenance.json`, pass `python scripts/fast_check.py`, and avoid private paths, credentials, and personal integrations. Do not add a skill merely because it exists elsewhere: it needs a portable input, output, and honest fallback.

Keep `skills/` and `packages/` canonical. After changing Context skills or its CLI, run `python scripts/project_context_plugin.py` and commit the resulting Claude projection.
