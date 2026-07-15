# Project status

## Release

- Public version: `0.1.1-beta`
- Codename: `Force of Will`
- Next beta: `0.2.0-beta — Ponder`
- Future major release: `1.0 — NicolAI Bolas`

## Current development line

Sprint `12.2a` introduces the executable Judge Tool Gateway.

Completed in this milestone:

- typed read-only tool contracts;
- executable Oracle, rules, rulings, legality, and conversation-context tools;
- source provenance and version reporting;
- bounded shared investigation budgets;
- in-memory source-aware cache;
- explicit unavailable responses for planned providers;
- diagnostic REST endpoint;
- first Tactician evidence refresh through the gateway;
- focused source-independent CI coverage.

## Next development line

Sprint `12.2b` will focus on conversational strategic orchestration:

- play-sequence and combo-follow-up intents;
- active strategic state;
- independent Tactician synthesis;
- warmer interactive responses;
- smart ambiguity handling;
- factual claim verification after synthesis.

## Known limitations

- The Tactician does not yet plan arbitrary multi-query investigations.
- Combo reconstruction covers only a narrow generic family.
- Commander Spellbook is not connected.
- EDHREC-style statistics remain permission-gated.
- A full deck analyzer and collection provider are not yet implemented.
- Some Judge fallbacks may still require stronger second-pass validation.
