# API contract

MagicAI exposes a versioned additive HTTP contract for the Judge beta UI.

## Versions

- Project version: package release version.
- API contract version: compatibility policy for HTTP endpoints.
- JudgeResult schema version: shape and semantics of structured Judge answers.

`GET /meta` exposes all three values. Every successful `/ask` response and every structured error includes `schema_version`.

## Compatibility policy

Within JudgeResult schema `1.x`:

- existing fields will not be removed or renamed;
- new optional fields may be added;
- enum values may only be added when clients can safely treat unknown values as informational;
- `answer` and `session_id` remain available for legacy clients.

A future incompatible change requires schema `2.0`.

## Endpoints

### `GET /meta`

Returns contract versions, supported Judge statuses, origins and confidence values.

### `GET /health`

Returns:

- whether required factual sources are ready;
- whether all optional sources are available;
- whether Ollama and the configured model are available;
- whether the service has full functionality or is operating in degraded deterministic mode.

`ready=true` means the required local factual sources are usable.
`full_service=true` additionally requires Ollama and the configured model.

### `POST /ask`

Returns a versioned `JudgeResult` plus `session_id`.

### Errors

Errors use this envelope:

```json
{
  "schema_version": "1.0",
  "error": {
    "code": "invalid_request",
    "message": "The request payload is not valid.",
    "retryable": false,
    "details": []
  }
}
```

Known codes include:

- `invalid_request`
- `llm_unavailable`
- `http_error`
- `internal_error`

The UI should use `code` for behavior and `message` for display.

---

## TacticianResult 0.1

El perfil estratégico se expone mediante `POST /tactician/ask`. Tactician no
recupera fuentes por sí mismo: ejecuta primero al Juez sobre una copia de la sesión y
consume el `JudgeResult` resultante.

Campos adicionales:

- `authority: tactician`
- `origin: tactician_strategy`
- `synergies`
- `risks`
- `authority_trace`
- `judge_result`

El endpoint factual `POST /ask` sigue siendo compatible. Los resultados del Juez
pueden incluir además `reviewed_by`, `review_challenges` y `authority_trace` cuando
una respuesta LLM haya pasado por revisión del Estratega.
