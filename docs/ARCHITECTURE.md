# MagicAI architecture

## Core rule

> The Judge owns factual authority and source access. The Tactician owns strategic investigation. The Critic rejects unsupported conclusions.

The source boundary is a trust boundary. It must not prevent the Tactician from asking repeated, increasingly precise questions.

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
    │   └─ validation and safe fallback
    │
    └─ Tactician
        ├─ strategic intent classification
        ├─ evidence-gap detection
        ├─ combo and synergy analysis
        ├─ Judge challenges
        └─ recommended lines and risks
```

## Judge source gateway

The Judge exposes capabilities instead of exposing raw source access to strategic profiles. Current and planned capabilities are published by `GET /meta`.

Authority levels:

- `official_card_data`: Scryfall Oracle snapshot.
- `official_rules`: Comprehensive Rules snapshot.
- `official_rulings`: Scryfall rulings snapshot.
- `community_combo_candidate`: Commander Spellbook candidate requiring revalidation.
- `statistical`: authorized EDHREC-style statistics, never rules authority.
- `user_data`: local collection, deck, preferences, or metagame.

## Automatic handoff

`POST /ask` first calls the Judge. When the Judge returns `strategy_required` and `auto_handoff=true`, the boundary answer is replaced by a Tactician result in the same conversation turn.

The previous active card package is preserved before the Judge processes the new turn. Referential questions such as:

```text
And does it combo with Ghave and Ashnod's Altar?
```

can therefore inherit the previously validated `Young Wolf` card package.

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

The Tactician should continue investigating when evidence is incomplete. A later planner will use a bounded query budget rather than a fixed one-shot package. Missing tools must be reported through the capability registry, not silently guessed.
