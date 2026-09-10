# Architecture explanation

The scheduler separates collection from publication so an interrupted collection cannot publish a partial result.

# CLI schema

| Command | Arguments |
| --- | --- |
| `context-engineering references <target-repo-root>` | target repository root |
