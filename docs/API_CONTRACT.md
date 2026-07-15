# API contract

Current API contract version: `1.4`.

## Stable result families

- Judge results use JudgeResult schema `1.0`.
- Tactician results use TacticianResult schema `0.3`.
- Judge tool results use JudgeToolResult schema `1.0`.

## Main endpoints

- `GET /`
- `GET /meta`
- `GET /health`
- `POST /ask`
- `POST /tactician/ask`
- `POST /judge/tools/execute`
- conversation history endpoints under `/conversations`

## Judge Tool Gateway endpoint

`POST /judge/tools/execute` executes one read-only Judge-owned capability.

Example:

```json
{
  "tool": "rules_lookup",
  "arguments": {
    "identifiers": ["702.93", "701.21"]
  },
  "purpose": "verify_undying_sacrifice",
  "result_limit": 8
}
```

The endpoint is intended for local diagnostics, future UI tooling, and controlled strategic orchestration. It does not allow arbitrary files, shell commands, provider URLs, or network access.

A `session_id` may be supplied only when `conversation_context` requires an existing persisted conversation.

## Capability discovery

`GET /meta` exposes:

- executable status;
- authority level;
- provider;
- read-only status;
- accepted argument names;
- result limit;
- planned and permission-gated capabilities.

Unavailable capabilities return a structured result instead of being guessed.
