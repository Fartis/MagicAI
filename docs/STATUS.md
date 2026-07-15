# Project status

## Release

- Public version: `0.1.1-beta`
- Codename: `Force of Will`
- Next beta: `0.2.0-beta — Ponder`
- Future major release: `1.0 — NicolAI Bolas`

## Current development line

Sprint `12.2b` introduces structured input reasoning and conversational strategic orchestration.

Completed in this milestone:

- speech-act and strategic-intent analysis;
- deterministic claim extraction;
- bounded multi-tool investigation plans;
- claim verdicts with source identifiers;
- independent Tactician synthesis instead of Judge-answer relay;
- conversational correction of user hypotheses;
- persisted strategic conversation context;
- play-sequence, disruption, and requirements follow-ups;
- TacticianResult schema `0.4` and API contract `1.5`;
- focused input-reasoning and conversation-state regressions.

## Next development line

Sprint `12.3` will focus on general autonomous investigation planning:

- broader claim decomposition;
- iterative evidence-gap detection;
- evidence sufficiency scoring;
- alternative and counterexample search;
- configurable investigation depth;
- wider strategic families beyond the current deterministic vertical slices.

## Known limitations

- Multi-query planning is implemented for supported concepts, but is not yet general across arbitrary interactions.
- Combo reconstruction covers only a narrow generic family.
- Commander Spellbook is not connected.
- EDHREC-style statistics remain permission-gated.
- A full deck analyzer and collection provider are not yet implemented.
- Some Judge fallbacks may still require stronger second-pass validation.
