# MagicAI HTTP contract

## Versions

- API contract: `1.2`
- JudgeResult schema: `1.0`
- TacticianResult schema: `0.2`

## Endpoints

```text
GET    /                         service metadata
GET    /meta                     contracts, profiles, codenames, capabilities
GET    /health                   source and Ollama health
POST   /ask                      Judge with optional automatic handoff
POST   /tactician/ask            explicit Tactician request
GET    /conversations            local history
GET    /conversations/{id}       conversation detail
PATCH  /conversations/{id}       rename conversation
DELETE /conversations/{id}       delete conversation
```

## Ask request

```json
{
  "question": "And does it combo with Ghave and Ashnod's Altar?",
  "session_id": "optional-session-id",
  "auto_handoff": true
}
```

`auto_handoff` defaults to `true`. Set it to `false` only for diagnostics that need the raw `strategy_required` Judge boundary.

## Strategic response fields

A handoff response remains compatible with the Judge evidence fields and may add:

```json
{
  "authority": "tactician",
  "strategy_intent": "combo_detection",
  "combo_classification": "infinite_combo",
  "combo_steps": [],
  "outcomes": [],
  "synergies": [],
  "risks": [],
  "inherited_cards": ["Young Wolf"],
  "judge_queries": [],
  "judge_result": {}
}
```
