# README rubric

Use this rubric for Audit mode and for skill-improvement trials. Grade each item
0-3, then translate to a letter grade.

## Table of Contents

- [Scoring](#scoring)
- [Criteria](#criteria)
- [Common failure patterns](#common-failure-patterns)
- [Trial report format](#trial-report-format)

## Scoring

- **3**: strong; works for a cold reader.
- **2**: usable; minor gaps or rough edges.
- **1**: present but weak, buried, stale, or confusing.
- **0**: missing or actively harmful.

Letter guide:

| Score | Grade |
|---:|---|
| 25-27 | A |
| 22-24 | B |
| 18-21 | C |
| 14-17 | D |
| 0-13 | F |

## Criteria

### 1. Orientation

The README quickly explains what the project is, who it is for, and why it
exists. A cold reader should not need to infer the purpose from install commands
or feature lists.

### 2. First success path

The README gives a short path to a meaningful result. Commands are ordered,
copy-pasteable, and include prerequisites only when needed.

### 3. Journey shape

The README progresses from orientation to first success to mental model to
reference. It does not start with architecture, configuration, or implementation detail before the reader knows why they matter.

### 4. Code-backed accuracy

Claims, examples, commands, and API descriptions match the repo. The README does
not invent usage examples or preserve stale behavior.

### 5. Command quality

Recommended commands are discoverable from repo metadata or verified directly.
Destructive, expensive, environment-specific, registry-install, host-mutating,
or external-service commands are labeled honestly.

### 6. Information architecture

The README separates quickstart, concepts, workflows, reference, and deeper docs.
It links out instead of becoming a dumping ground.

### 7. Voice and anti-slop

The writing sounds like a helpful maintainer. It avoids marketing language,
generic AI phrasing, fake enthusiasm, perfectly symmetric filler, and decorative
noise.

### 8. Practical examples

Examples come from real tests, CLI help, docs, demos, or source usage. They show
expected output or success signals when helpful. API, MCP, SDK, and CLI-tool
examples are checked against current signatures, schemas, help, or tests.

### 9. Maintenance friendliness

The README is easy to update. Generated sections, repo maps, version numbers,
and command references have clear sources or are kept small enough to maintain.

## Common failure patterns

- **Feature soup**: capabilities listed before the reader knows why they matter.
- **Setup maze**: prerequisites, installation, local testing, and development are
  mixed together.
- **Concepts first**: architecture or configuration appears before first success.
- **AI brochure voice**: `powerful`, `robust`, `seamless`, `comprehensive`, and
  similar words stand in for specifics.
- **Command drift**: commands are guessed, outdated, duplicated, or inconsistent
  with the repo's task runner.
- **Install provenance drift**: registry install commands are inferred from
  package metadata without verifying publication or offering a source install, or
  the caveat appears only in the final response and not the README.
- **Reference overload**: every option and command is in the README even when a
  docs page would serve better.
- **Personality removal**: an update deletes useful maintainer voice and replaces
  it with sterile template prose.

## Trial report format

```markdown
## Repo: name
Mode: init|update
Grade: B (23/27)

### Passes
- Criterion: evidence.

### Failures
- Criterion: issue, evidence, suggested skill patch if this is a recurring
  failure.

### Notes
- Facts left unverified.
- Content preserved or intentionally omitted.
```
