# Project status

## Release

- Public version: `0.1.1-beta`
- Codename: `Force of Will`
- Next beta: `0.2.0-beta — Ponder`
- Future major release: `1.0 — NicolAI Bolas`

## Current development line

Sprint `12.2d` adds response orchestration and the first full Tactician Conversation Gauntlet.

Completed in this milestone:

- explicit `judge_led`, `tactician_led`, and `hybrid` response modes;
- rules and mechanic questions led by the Judge factual core;
- strategic questions led by the Tactician;
- mixed rules-and-strategy questions handled through a hybrid path;
- deterministic factual-core extraction and coverage checks;
- protection against replacing a correct Judge answer with a generic combo template;
- combo classification suppressed when the current turn is not asking about a combo;
- `mechanic_resolution` intent for questions such as sacrificing Young Wolf;
- session-aware Spanish and English output preserved across all response fields;
- 40 data-driven conversational scenarios covering 58 turns;
- controlled Judge and Judge Tool Gateway fixtures for fast CI;
- semantic, negative, evidence, language, and continuity assertions;
- JSON and HTML conversation-gauntlet reports;
- a review-only command for promoting exported UI feedback into candidate cases;
- TacticianResult schema `0.6` and API contract `1.7`.

## Next development line

Sprint `12.3` will focus on the general autonomous investigation planner:

- hypothesis decomposition;
- iterative evidence requests based on unresolved claims;
- evidence-sufficiency scoring;
- alternative and counterexample search;
- bounded research loops;
- reusable investigation traces beyond the currently supported interaction families.

## Known limitations

- Casual-language normalization is conservative and currently covers a bounded vocabulary.
- Factual-core templates are implemented for the first rules and combo families, not arbitrary Magic interactions.
- Fixture-mode semantic assertions are deterministic; local Ollama mode remains a manual or scheduled evaluation.
- Combo reconstruction covers only narrow generic families.
- Commander Spellbook is not connected.
- EDHREC-style statistics remain permission-gated.
- A full deck analyzer and collection provider are not yet implemented.
