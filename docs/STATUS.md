# Project status

## Release

- Public version: `0.1.1-beta`
- Codename: `Force of Will`
- Next beta: `0.2.0-beta — Ponder`
- Future major release: `1.0 — NicolAI Bolas`

## Current development line

Sprint `12.3a2` closes the land-type investigation line with metadata consistency and renderer generalization.

Completed in this milestone:

- structured hypothesis decomposition from user claims, strategic intent, concepts, and active cards;
- explicit required-evidence tokens for Oracle cards and Comprehensive Rules sections;
- deterministic sufficiency scores for each hypothesis and the overall investigation;
- reactive fallback searches when exact Oracle or rules lookups leave evidence unresolved;
- alternative-search and counterexample-search phases selected from the user's speech act;
- enforcement of total-call, per-tool, repeated-request, and elapsed-time budgets;
- full reusable `investigation_trace` output with request phases, score changes, errors, cache state, and budget snapshots;
- Oracle evidence refresh folded into the same auditable planner loop;
- casual Spanish validation markers such as `verdad` and `cierto` recognized as requests to challenge a premise;
- pytest restricted to the active `tests/` tree so historical `backups/` do not collide during collection;
- TacticianResult schema `0.7` and API contract `1.8`;
- rules questions involving land types, mana abilities, layers, dependencies, and timestamps are classified as Judge-led;
- a reserved Comprehensive Rules package pins 305.6, 305.7, 305.8, 611.3, 613.1d, 613.7, 613.8a, and 613.8b;
- a generic deterministic renderer resolves a nonbasic-land type setter against additive basic-land-type effects;
- dependency is evaluated before timestamp when applying the setter removes the source ability of a nonbasic land;
- answer obligations now cover each requested land category, resulting mana colors, and reversed entry order;
- an `insufficient_evidence` Judge result cannot be reported as `judge_verified` or `answer_complete`;
- deterministic answers and their Tactician metadata now agree on completeness, confidence, and evidence verification;
- answer-contract checks recognize singular/plural basic land types and general mana outcomes rather than one exact phrase;
- the Oracle-pattern renderer accepts both `a` and `an` before a basic land type and is regression-tested with fictional card names and different land types.

## Next development line

Sprint `12.3b` will generalize adaptive research policies:

- multi-step follow-up policies beyond one fallback per hypothesis;
- contradiction-aware evidence comparison;
- dynamic hypothesis expansion from newly recovered evidence;
- query prioritization by expected information gain and remaining budget;
- broader regression cases outside the current deterministic interaction families.

## Known limitations

- Casual-language normalization is conservative and currently covers a bounded vocabulary.
- Factual-core templates are implemented for the first rules and combo families, not arbitrary Magic interactions.
- Fixture-mode semantic assertions are deterministic; local Ollama mode remains a manual or scheduled evaluation.
- Combo reconstruction covers only narrow generic families.
- Commander Spellbook is not connected.
- EDHREC-style statistics remain permission-gated.
- A full deck analyzer and collection provider are not yet implemented.
