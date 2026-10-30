# Anti-Hallucination Protocol

Apply these three constraints to all research output. They come from Anthropic's "Reduce Hallucinations" documentation and rubric-based evaluation best practices.

## 1. Allow "I don't know"

If the code, docs, or sources don't contain enough information to answer a question, say so explicitly. Do not fill gaps with plausible-sounding reasoning. Phrases to use:

- "I couldn't verify this from the code"
- "This file/function doesn't exist in the codebase — the research may be outdated"
- "I found partial evidence but can't confirm the full picture"

## 2. Cite everything

Every factual claim must have a source. For code research:

- **File path + line number**: `src/service.py:42`
- **Function/class name**: `score_items()` in `service.py`
- **PR diff reference**: "From the diff, lines +42-+58 add..."
- **Doc reference**: "Per the README in `docs/`..."

If a claim can't be cited, retract it. A statement that "sounds right" but has no source is worse than no statement.

## 3. Quote before analyzing

When discussing code behavior, extract the actual code first, then analyze. Do not paraphrase code from memory — read it, quote it, then explain.

```
# Good:
The function signature is:
```python
def score_items(user_id, ad_ids, ml_config, use_canary_scores=False):
```
Note: it does NOT accept a context DTO — this would need to be added.

# Bad:
The score_items function takes user_id, ad_ids, and a context parameter...
(← never verified, may be wrong)
```

## When to relax

These constraints are for **research mode** — factual investigation where accuracy matters. They reduce creative output, so don't apply them to brainstorming, drafting, or exploratory conversation.
