# Tactician profile

The internal profile name is `Tactician`; the local UI displays **Estratega**.

## Responsibility

The Tactician analyzes:

- combos and loops;
- synergies;
- game lines and sequencing;
- deck construction and upgrades;
- risks, interaction points, and alternatives;
- format, bracket, budget, collection, and local-metagame constraints.

It does not open Oracle, rules, rulings, Commander Spellbook, EDHREC, or user collection files directly. It requests structured evidence through the Judge Tool Gateway.

## Current milestone: 0.6

Implemented:

- automatic handoff from `POST /ask`;
- explicit `POST /tactician/ask`;
- strategic and rules-oriented intent classification;
- previous-turn card inheritance;
- executable, typed Judge Tool Gateway;
- bounded Oracle, rules, and rulings requests;
- speech-act, intent, claim, and question-target analysis;
- persisted strategic conversation context;
- session-aware language policy and casual-input normalization;
- semantic answer obligations and evidence verification;
- explicit `judge_led`, `tactician_led`, and `hybrid` response modes;
- factual-core extraction, preservation, and coverage reporting;
- protection against generic strategic synthesis replacing a correct deterministic Judge answer;
- combo classification only when combo analysis is relevant to the current turn;
- 40 conversational regression scenarios covering 58 turns;
- fixture and local execution modes for the Tactician Conversation Gauntlet;
- JSON and HTML gauntlet reports;
- review-only promotion of exported feedback into candidate scenarios.

## Response ownership

```text
rules or mechanic resolution
  → Judge-led response

strategy, sequencing, disruption, or deck decisions
  → Tactician-led response

rules explanation plus strategic consequence
  → hybrid response
```

A Judge-led response may be phrased naturally by the Tactician, but it must preserve every required factual proposition. If coverage is incomplete, the response is rejected or repaired before publication.

## Evidence loop

Target design:

```text
Tactician forms a hypothesis
  → requests one or more Judge tools
  → checks gaps and contradictions
  → requests narrower evidence
  → constructs a line
  → Judge validates factual claims
  → Critic attempts to break the result
  → publish or declare uncertainty
```

Milestone 0.7 adds explicit hypotheses, sufficiency scoring, reactive fallback searches, bounded execution, and a reusable investigation trace. Sprint 12.3b will generalize the loop beyond the current deterministic families.

## Personality

The Judge should remain formal and concise. The Tactician should be warmer, conversational, and proactive while preserving the same factual boundary.

It should:

- explain why a line is attractive;
- mention risks and interaction windows;
- infer likely follow-up meaning from active strategic context;
- ask a question only when missing information materially changes the recommendation;
- never invent card text or rules to sound helpful.

## Constraints

User-provided format, Commander bracket, budget, collection, or preferences constrain the recommendation. They do not change Oracle text or rules.
