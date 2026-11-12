# README workflow

Use this workflow after loading `readme-improver/SKILL.md`.

## Table of Contents

- [1. Pick the mode](#1-pick-the-mode)
- [2. Scope the README](#2-scope-the-readme)
- [3. Discover repo facts](#3-discover-repo-facts)
- [4. Init mode structure](#4-init-mode-structure)
- [5. Update mode structure](#5-update-mode-structure)
- [6. Audit mode output](#6-audit-mode-output)
- [7. Voice pass](#7-voice-pass)

## 1. Pick the mode

- **Init**: no README exists, or the user explicitly wants a from-scratch rewrite.
- **Update**: a README exists and should be improved in place.
- **Audit**: the user asks for a grade, critique, or plan only.

If the mode is ambiguous, choose the least destructive path. Audit before editing.

## 2. Scope the README

Start from the directory where `README.md` lives or will live.

- Root README: explain the whole repo.
- Nested README: explain only that package/module/subtree unless the user says
  otherwise.
- Multi-product repo: name each audience path instead of forcing one linear story.
- Root index repo: explain how to choose/open/create subprojects; let nested
  READMEs explain individual subprojects.
- Generated-index repo: document the generation/update process and do not edit
  generated blocks unless the user asks to change the generator.

Read local context before repo-wide context:

1. `AGENTS.md` / `CLAUDE.md` near the README scope.
2. Existing `README.md`, `docs/`, `CONTRIBUTING.md`, `CHANGELOG.md`.
3. Task and package files: `.mise.toml`, `justfile`, `Makefile`, `pyproject.toml`,
   `Cargo.toml`, `package.json`, `go.mod`, lockfiles, CI workflows.
4. Entry points: CLI modules, binaries, app directories, exported packages, tests,
   examples, demo assets.

## 3. Discover repo facts

Find facts that answer these questions:

- What is this project in one sentence?
- Who uses it: end users, operators, contributors, agents, or only the repo owner?
- What is the smallest useful success path?
- What commands are blessed by the repo, and which are only local shortcuts?
- What concepts does a reader need after first success?
- What details belong in reference tables or linked docs instead of the README?
- What gotchas would make a newcomer or agent go sideways?

Prefer verified facts. Use `--help`, task files, static metadata, tests,
examples, and existing docs. If a command cannot be run safely or cheaply, label
it with one of these statuses: `verified by running`, `verified by metadata`,
`not run: unsafe/expensive`, `not run: trust required`, or `not verified`.

When no root task/package file exists, scan one level down for repeated project
files and document commands with the required working directory. When a task is
central to quick start, inspect its task file or CLI source instead of only
checking that the task name exists. For commands that initialize, generate,
install hooks, write config, or install services, record the exact files, scopes,
or external systems they change and keep repeated command mentions consistent.

For install docs, distinguish source-checkout commands from published-package
commands. If package-registry publication was not verified, label the registry
install as unverified in the README or pair it with the source-checkout path.
For package-manager setup commands such as `npm install`, `uv sync`, or `bundle
install`, mention local dependency writes or network needs when that matters to
first success.

## 4. Init mode structure

Create a README using this shape, adapting section names to the repo:

```markdown
# Project name

One sentence: what it is and who it helps.

A short paragraph that explains why it exists. Keep this concrete.

## Quick start

Copy-pasteable first-success path.

## What you just ran

Explain the few moving parts introduced by the quick start.

## How the repo is organized

Small repo map or narrative. Include only paths that help the reader move.

## Common workflows

2-5 practical workflows with commands.

## Configuration

Only if configuration is part of normal use.

## Development

Setup, validation, tests, release notes.

## Troubleshooting

Only real gotchas or likely first-run failures.

## Further reading

Links to deeper docs.
```

Do not force every section. A tiny archive repo may need only a title, purpose,
index, and contribution/export notes. A multi-entrypoint CLI may need `Pick your
path` before `Quick start`. A daemon/service should show a one-off validation
command before `install`, `enable`, or background-start commands.

If package metadata or build tooling fails because `README.md` is missing, write
the candidate README first using source/static facts, then retry the cheap help or
version command and record both the initial block and the post-write result.

## 5. Update mode structure

1. Read the current README once for intent and voice. Name any distinctive
   maintainer positioning, warnings, jokes, or terms of art before editing.
2. Make a gap list:
   - missing first-contact explanation
   - missing or buried quick start
   - stale commands
   - duplicated setup sections
   - feature inventory before reader path
   - useful detail trapped in the wrong section
   - generated regions that should not be hand-edited
   - overlapping claims in docs that may drift
   - AI-vibe language
3. If the existing README already scores roughly B or better, prefer a surgical
   patch plan and representative edits over a full template replacement.
4. Preserve accurate, specific, human-written content.
5. Reorder around a reader journey, but use ordinary public headings; never leak internal planning labels such as `First Contact`, `Black Triangle`, or `Hairball` into generated README text.
6. Shorten overgrown sections by linking to existing docs or creating a suggested
   follow-up doc path. Keep one small example in README and make docs/reference
   pages the source of truth for long tables.
7. Confirm the scoped `README.md` exists at the target path. For Init mode, do
   not finish without writing it or reporting why writing is blocked.
8. List the top 2-4 journey gaps found and mark each as fixed, deferred, or left
   unchanged with a reason.
9. If related non-README docs are stale, decide the disposition: fix if in scope,
   mention as deferred follow-up, or avoid linking until corrected. Prefer noting
   docs drift in the final response unless it directly affects the README path.
10. Add a short verification note in the final response using the verification
   status labels above.

## 6. Audit mode output

Use this format:

```markdown
## Grade

Overall: B-

## What works

- Specific strength with section/path reference.

## What breaks the journey

- Finding: concrete issue.
  - Evidence: quote or section reference.
  - Fix: direct action.

## Suggested rewrite plan

1. First edit.
2. Second edit.
3. Third edit.
```

Avoid generic writing advice. Every finding needs a concrete fix target.

## 7. Voice pass

Before finalizing, read the README as if explaining it to a colleague.

Cut or rewrite:

- paragraphs that repeat the heading
- abstract claims without evidence
- long preambles before commands
- "easy/simple" claims
- formal phrases like `utilize`, `facilitate`, `enable users to leverage`
- conclusion sections that say nothing new
- hand-maintained index tables with no update rule or source of truth
- generated blocks that are stale without a regeneration note

Keep:

- honest caveats
- specific tradeoffs
- repo-owner personality when it helps orientation
- exact commands and examples
