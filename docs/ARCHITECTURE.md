# MagicAI architecture

## Core rule

> The Judge owns factual authority and source access. The Tactician owns strategic investigation. The Critic rejects unsupported conclusions.

The source boundary is a trust boundary, not a one-shot limitation. The Tactician may issue repeated structured requests through the Judge.

## Main components

```text
UI / REST API
    │
    ▼
Conversation manager
    │
    ▼
Request orchestrator
    ├─ Judge
    │   ├─ context builder
    │   ├─ source retrieval
    │   ├─ deterministic renderers
    │   ├─ LLM explanation fallback
    │   ├─ validation and safe fallback
    │   └─ Judge Tool Gateway
    │       ├─ Oracle
    │       ├─ Comprehensive Rules
    │       ├─ rulings
    │       ├─ legality
    │       └─ conversation context
    │
    └─ Tactician
        ├─ speech-act and strategic intent analysis
        ├─ claim extraction and verdicts
        ├─ bounded investigation planning
        ├─ combo and synergy analysis
        ├─ Judge-tool requests
        ├─ conversational synthesis
        ├─ Judge challenges
        └─ recommended lines and risks
```

## Judge Tool Gateway

The gateway converts source adapters into typed, read-only capabilities. Every result records authority, provider, source version, arguments, purpose, latency, cache state, warnings, and budget state.

Current executable authority levels:

- `official_card_data`: local Scryfall Oracle snapshot.
- `official_rules`: local Comprehensive Rules snapshot.
- `official_rulings`: local Scryfall rulings snapshot.
- `session_state`: bounded local conversation state.

Future authority levels:

- `community_combo_candidate`: Commander Spellbook candidate requiring full revalidation.
- `statistical`: authorized statistics, never rules authority.
- `user_data`: local collection, deck, preferences, or metagame.

Planned providers remain visible but cannot execute until an authorized handler is installed.

## Automatic handoff

`POST /ask` first calls the Judge. When the Judge returns `strategy_required` and `auto_handoff=true`, the boundary answer is replaced by a Tactician result in the same conversation turn.

The previous active card package is preserved before the Judge processes the new turn. Referential questions can therefore inherit previously validated cards.

The Tactician can then refresh named cards through `oracle_lookup` without direct source access.

## Combo proof model

A combo claim must describe:

1. Initial state.
2. Actions and costs.
3. Zone and object transitions.
4. State restored for repetition.
5. Net output per iteration.
6. Interruption points and assumptions.

Classification values:

- `infinite_combo`
- `bounded_loop`
- `repeatable_synergy`
- `one_shot_interaction`
- `non_combo`
- `insufficient_information`

## Resilience

The Tactician should continue investigating when evidence is incomplete. The gateway supplies bounded query budgets, explicit capability failures, and source-aware caching. Missing tools must be reported rather than silently guessed.

## Structured input reasoning

The Tactician analyzes the user's message before requesting evidence. It records a compact audit trail containing the speech act, detected claims, planned queries, claim verdicts, and a concise reasoning summary.

This is intentionally structured and testable. It is not a free-form chain-of-thought log.

When the Judge already returns a factual answer, the Tactician still performs its own strategic synthesis rather than relaying that prose unchanged.
