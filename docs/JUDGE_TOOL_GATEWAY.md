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

## Tactician planner use

Sprint 12.3a executes Judge-tool requests through an autonomous but bounded investigation loop. The planner first decomposes the turn into hypotheses, assigns explicit Oracle or rules evidence requirements, and runs the exact lookup plan. If a hypothesis remains unresolved, it may issue one narrower `rules_search` or `oracle_search` fallback while preserving the same shared budget.

`investigation_plan` records the initial goals, requests, and hypotheses. `investigation_trace` records every executed phase, the hypotheses affected, evidence counts, sufficiency before and after the call, cache state, errors, and budget snapshots. Missing or unavailable evidence remains explicit and reduces `judge_verified` rather than being silently guessed.


## Sprint 12.3a1 land-type layer hardening

Rules questions that combine land types, mana abilities, layers, dependency, and
timestamp now reserve a complete eight-rule evidence package before incidental
Oracle-derived queries can consume the bounded rules context. The Tactician
planner mirrors the same evidence requirements in its hypotheses.

A generic deterministic Judge renderer recognizes three reusable Oracle shapes:

- a global effect that sets nonbasic lands to a basic land type;
- a controller-scoped effect that adds every basic land type;
- a static ability on a nonbasic land that adds one basic land type globally.

The renderer applies dependency when the subtype-setting effect removes the
nonbasic land source's printed ability, then applies timestamp order between
independent layer-4 effects. It does not branch on exact card names.

## Sprint 12.3a2 metadata consistency

The deterministic renderer remains a bounded rules engine rather than a card-name
lookup table. Its contract validator now checks reusable game concepts such as
layer number, basic-land-type outcomes, mana outcomes, dependency, and changed
timestamp order. It no longer depends on one exact pluralization or sentence.

The Oracle-shape parser also accepts both `a` and `an` before a basic land type.
A regression using fictional names, a Swamp setter, and an Island global adder
ensures that the branch is selected from recovered Oracle text and rules evidence.
