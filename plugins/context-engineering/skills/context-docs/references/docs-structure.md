# Documentation structure

Classify content by reader intent before choosing a location:

| Intent | Location | Purpose |
| --- | --- | --- |
| Learn a concept | `explanation/` | Explain enduring design and tradeoffs. |
| Look up a fact | `reference/` | Record commands, interfaces, schemas, and configuration. |
| Follow a repeatable agent procedure | a proposed skill | Keep decision-making procedures out of generated docs. |
| Onboard a new user | the established README or onboarding surface | Preserve the repository's existing owner. |

Existing repository conventions win. For a new managed tree, keep human reading order in `docs/README.md` and agent routing in `docs/AGENTS.md`.
