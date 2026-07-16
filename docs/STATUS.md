# Project status

## Release

- Public version: `0.1.1-beta`
- Codename: `Force of Will`
- Next beta: `0.2.0-beta — Ponder`
- Future major release: `1.0 — NicolAI Bolas`

## Current development line

Sprint `12.2c` adds conversational understanding, language consistency, and semantic answer validation.

Completed in this milestone:

- session-aware Spanish and English language policy;
- English MTG names and keywords excluded from strong language evidence;
- shared casual-language normalization for the Judge and Tactician;
- professional Judge responses after colloquial user input;
- rules-oriented Tactician intents;
- open questions separated from factual claims;
- evidence-aware mechanic-equivalence verdicts;
- deterministic answer obligations and forbidden-drift checks;
- corrected `judge_verified` and confidence derivation when evidence is complete;
- TacticianResult schema `0.5` and API contract `1.6`;
- first data-driven multi-turn Tactician conversation regression.

## Next development line

Sprint `12.2d` will build the wider Tactician Conversation Gauntlet:

- reusable multi-turn scenario runner;
- controlled Judge Tool Gateway fixtures;
- semantic and negative assertions;
- optional Ollama execution mode;
- JSON and HTML failure reports;
- manual promotion of exported feedback into reviewed regression candidates.

Sprint `12.3` will then focus on general autonomous investigation planning.

## Known limitations

- Casual-language normalization is conservative and currently covers a bounded vocabulary.
- Semantic answer contracts are implemented for the first rules-oriented and combo-requirement families.
- Multi-query planning is not yet general across arbitrary interactions.
- Combo reconstruction covers only narrow generic families.
- Commander Spellbook is not connected.
- EDHREC-style statistics remain permission-gated.
- A full deck analyzer and collection provider are not yet implemented.
