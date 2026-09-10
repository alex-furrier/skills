# Session Sources

## Current session

Read the full available conversation from the beginning. Early corrections,
failed approaches, and decisions often contain more durable signal than the
final summary.

## Past session

When the user supplies a JSONL file, identify the runtime schema before
extracting records:

- **Claude Code**: keep records whose top-level `type` is `user` or `assistant`;
  accept older records whose role is stored under `message.role`.
- **Pi**: keep `type: "message"` records whose `message.role` is `user` or
  `assistant`.
- **Codex**: keep `response_item` records when `payload.type` is `message` and
  `payload.role` is `user` or `assistant`. Also retain `function_call`,
  `custom_tool_call`, `function_call_output`, and `custom_tool_call_output`
  payloads so the call/result sequence remains reconstructable.

For Claude Code and Pi, `message.content` may be a string or a block array. For
Codex messages, extract `payload.content[].text` from `input_text` and
`output_text` blocks; read call names/inputs and their corresponding outputs
from the retained non-message payloads. Across runtimes, extract:

- user text and corrections;
- assistant text, diagnoses, and summaries;
- tool calls and their inputs;
- tool results embedded in user block arrays.

Skip developer/system prompts, private reasoning, generated harness context,
session metadata, and file-history bookkeeping. Retain tool calls and results
only as supporting evidence; failed invocations followed by a successful
sequence are useful workflow evidence.

For files over roughly 1,000 lines, use a bounded parser rather than loading
raw JSONL into the conversation. Preserve the session identifier when
attribution is needed, but never expose private reasoning or secrets.
