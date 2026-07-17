# MagicAI roadmap

## Release targets

### 0.1.1 beta — Force of Will — current

The first public beta establishes the integrated Judge and Tactician foundation, persistent conversations, structured evidence, automated handoff, and repository-health basics.

### 0.2.0 beta — Ponder

The next integrated beta requires:

- reliable Judge answers for the covered families;
- source-grounded validation and safe failure;
- automatic Judge-to-Tactician handoff;
- resilient conversation continuity;
- iterative Tactician queries through the Judge Tool Gateway;
- formal combo reconstruction;
- useful local UI and persistent history;
- reproducible installation and evaluation.

### 1.0 — NicolAI Bolas

The first major release should add mature deck analysis, authorized strategic sources, collection awareness, broader format support, and production-grade packaging.

## Repository health — parallel track

- Fast pull request CI without Ollama or bulk sources.
- Clean tracked-file release packaging.
- Security, support, conduct, and pull request policies.
- Dependabot configuration.
- Explicit branch and release procedures.
- Later: test markers, static analysis, governance, maintainers, ADRs, and branch cleanup.

## Sprint 12 — Tactician integration

### 12.0 — Initial vertical slice — complete

- Tactician profile and API endpoint.
- Judge contradiction review.
- Basic role and synergy analysis.

### 12.1 — Automatic handoff and continuity — complete

- Automatic handoff from `/ask`.
- No duplicate conversation turns.
- Referential previous-card inheritance.
- Intent-specific combo boundary.
- Structured combo steps and outcomes.
- Generic Undying loop recognition.
- Judge capability registry.

### 12.2a — Executable Judge Tool Gateway — complete

- Typed tool requests and responses.
- Per-tool provenance, version, latency, cache state, and authority.
- Executable Oracle lookup and search.
- Executable rules lookup and search.
- Executable rulings, legality, and conversation-context tools.
- Bounded shared query budgets.
- Capability-missing responses.
- Read-only diagnostic REST endpoint.
- Initial Tactician Oracle refresh through the gateway.

### 12.2b — Input reasoning and conversational orchestration — complete

- Structured speech-act, intent, and claim analysis.
- Bounded multi-tool investigation plans.
- `play_sequence`, `combo_disruption`, `combo_requirements`, and `interaction_hypothesis` intents.
- Persisted active strategic conversation state.
- Independent Tactician synthesis instead of Judge-answer relay.
- Warm, interactive response style for supported families.
- Claim verdicts and evidence identifiers.
- Evidence-verification metadata.

### 12.2c — Conversational understanding and answer validation — complete

- Session-aware language policy.
- Shared casual-language normalization for Judge and Tactician.
- Professional Judge output regardless of user register.
- Rules-oriented Tactician intents.
- Question targets separated from factual claims.
- Semantic answer obligations and forbidden-drift checks.
- Evidence-aware `judge_verified` and confidence derivation.
- Seed data-driven multi-turn conversation regression.

### 12.2d — Response orchestration and Tactician Conversation Gauntlet — complete

- `judge_led`, `tactician_led`, and `hybrid` response arbitration.
- Deterministic factual-core extraction and preservation.
- Combo classification limited to combo-relevant turns.
- Reusable multi-turn scenario execution.
- Structured semantic and negative assertions.
- Controlled evidence fixtures and optional local mode.
- JSON and HTML reports.
- Manual promotion of reviewed UI feedback exports.
- 40 scenarios covering 58 turns.
- Young Wolf, Carrion Feeder, and The Ozolith reasoning regression.
- Ghave and Ashnod's Altar sequencing, requirements, and disruption regression.

### 12.3 — General autonomous investigation planner — in progress

#### 12.3a — Hypothesis and evidence loop — complete

- Structured hypothesis decomposition from claims, intents, concepts, and active cards.
- Explicit evidence requirements per hypothesis.
- Per-hypothesis and overall evidence-sufficiency scoring.
- Reactive `rules_search` and `oracle_search` fallback for unresolved evidence.
- Alternative or counterexample search selected from the user's speech act.
- Bounded time, total-query, per-tool, and repeated-request budgets.
- Full reusable investigation trace with phases, score changes, errors, cache state, and budget snapshots.
- TacticianResult schema `0.7` and API contract `1.8`.

#### 12.3a1 — Land-type layer investigation hardening — complete

- Rules-first classification for questions about layers, dependencies, timestamps, land types, and mana abilities.
- Reserved eight-rule evidence package for basic/nonbasic land type interactions.
- Generic deterministic renderer for subtype-setting and subtype-adding static effects.
- Dependency handling when a nonbasic land source loses its printed static ability.
- Timestamp comparison for independent layer-4 effects.
- Contract coverage for controlled basics, controlled nonbasics, opposing nonbasics, mana colors, and reversed entry order.
- `judge_verified` can no longer be true when the underlying Judge result is `insufficient_evidence`.
- Regression derived from the Blood Moon / Urborg / Dryad manual test without a card-name-specific exception.

#### 12.3a2 — Deterministic metadata consistency — complete

- Answer-contract checks align with the generic renderer vocabulary instead of exact sentence fragments.
- Singular and plural basic land types and concrete mana outcomes are recognized in Spanish and English.
- Successful deterministic Judge answers now propagate `answer_complete`, `judge_verified`, high confidence, and the evidence-verification authority trace consistently.
- Oracle pattern matching supports grammatically correct `a` / `an` basic-land-type text.
- A fictional-card regression proves that the renderer is driven by Oracle shapes and rules evidence rather than exact card names.

#### 12.3b — Generalized adaptive research policies — next

- Multi-step follow-up policies beyond one fallback per hypothesis.
- Contradiction-aware evidence comparison.
- Dynamic hypothesis expansion from newly recovered evidence.
- Query prioritization by expected information gain and remaining budget.
- Broader regression cases outside the current sacrifice, Undying, counters, and timing families.

### 12.4 — Formal combo verifier

- State graph.
- Costs and resources.
- Zones, targets, timing, and priority.
- State restoration.
- Net output.
- Interruption points.
- Infinite, bounded, synergy, and non-combo classifications.

### 12.5 — Commander Spellbook connector

- Official or permitted API client.
- Local cache and provenance.
- Candidate retrieval by cards or deck.
- Mandatory Oracle and rules revalidation.
- Drift detection.

### 12.6 — Deck analysis

- Curve, lands, and color sources.
- Ramp, card advantage, interaction, and protection.
- Engines, win conditions, and redundancy.
- Existing and near-complete combos.
- Budget and collection-aware alternatives.

### 12.7 — Authorized strategic statistics

- Provider abstraction.
- Authorized EDHREC integration or explicit user import.
- Popularity and synergy statistics clearly labeled as non-authoritative.

### 12.8 — User context

- Format and Commander bracket.
- Budget.
- Collection.
- Preferred play style.
- Local metagame.
- Infinite-combo preferences.

### 12.9 — Critic integration

- Structured challenges.
- Evidence contradiction checks.
- Second validation.
- Source-built fallback.

### 12.10 — Strategic Gauntlets

- Handoff Gauntlet.
- Conversation Reference Gauntlet.
- Combo Verification Gauntlet.
- Synergy Classification Gauntlet.
- Spellbook Drift Gauntlet.
- Judge–Tactician Disagreement Gauntlet.
