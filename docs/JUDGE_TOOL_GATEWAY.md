# Judge Tool Gateway

The Judge Tool Gateway is the controlled evidence interface used by strategic profiles.

## Trust boundary

The Tactician decides what must be investigated. The Judge owns every source adapter and returns structured, read-only evidence.

The gateway does not make strategic decisions. It preserves:

- provider identity;
- authority level;
- local source versions;
- arguments and purpose;
- latency;
- cache state;
- warnings and explicit failures;
- bounded investigation budgets.

## Executable tools

The first executable set is:

- `oracle_lookup`
- `oracle_search`
- `rules_lookup`
- `rules_search`
- `rulings_lookup`
- `legality_check`
- `conversation_context`

Planned or permission-gated providers remain visible in the capability registry but return an explicit unavailable result until an authorized adapter exists.

## Request contract

```json
{
  "tool": "oracle_lookup",
  "arguments": {
    "card_names": ["Young Wolf"]
  },
  "purpose": "verify_combo_component",
  "request_id": "optional-caller-id",
  "result_limit": 8
}
```

## Result contract

```json
{
  "schema_version": "1.0",
  "tool": "oracle_lookup",
  "status": "success",
  "authority": "official_card_data",
  "provider": "local_scryfall_oracle",
  "purpose": "verify_combo_component",
  "arguments": {
    "card_names": ["Young Wolf"]
  },
  "evidence": [],
  "source_versions": {},
  "warnings": [],
  "metadata": {},
  "error_code": "",
  "error_message": "",
  "elapsed_ms": 0.0,
  "cache_hit": false,
  "budget": {}
}
```

## Budgets

A strategic investigation can share one `JudgeToolBudget` across several calls. The budget limits:

- total tool calls;
- calls per tool;
- repeated identical requests;
- elapsed investigation time.

This prevents accidental loops without forcing the Tactician into a one-shot evidence package.

## Cache

Read-only source queries use a bounded in-memory cache keyed by:

- tool name;
- normalized arguments;
- requested result limit;
- local source-version fingerprint.

Conversation context is never cached.

## REST diagnostics

`POST /judge/tools/execute` exposes the same read-only contract for local diagnostics and future UI tooling. Strategic code should use `JudgeToolGateway` rather than opening files or repositories directly.
