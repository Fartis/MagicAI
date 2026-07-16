# API contract

Current API contract version: `1.7`.

## Stable result families

- Judge results use JudgeResult schema `1.0`.
- Tactician results use TacticianResult schema `0.6`.
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

## Tactician reasoning fields

TacticianResult `0.6` includes:

- `input_analysis`
- `claim_verdicts`
- `reasoning_summary`
- `queries_planned`
- `queries_completed`
- `judge_verified`
- `investigation_plan`
- `response_language`
- `language_policy`
- `answer_obligations`
- `answer_contract`
- `answer_complete`
- `response_mode`
- `response_orchestration`
- `factual_core`
- `factual_core_coverage`
- `factual_core_preserved`
- `strategic_extension_required`

`response_mode` is one of `judge_led`, `tactician_led`, or `hybrid`. A Judge-led response preserves the factual answer core; a Tactician-led response performs strategic synthesis; a hybrid response combines a Judge-owned rules explanation with a Tactician-owned strategic conclusion.

These fields expose a concise, structured audit trail. They are not a hidden chain-of-thought transcript. `answer_complete` means the generated answer satisfied its deterministic semantic obligations; `judge_verified` additionally requires supporting Judge-owned evidence.
