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

### 12.2b — Conversational strategic orchestration — next

- `play_sequence`, `combo_execution_order`, `combo_disruption`, and related intents.
- Active strategic conversation state.
- Independent Tactician synthesis instead of Judge-answer relay.
- Warm, interactive response style.
- Smart ambiguity handling.
- Factual claim verification after synthesis.

### 12.3 — Autonomous investigation planner

- Hypothesis decomposition.
- Multiple Judge queries per user request.
- Evidence sufficiency scoring.
- Alternative and counterexample search.
- Bounded time and query budgets.
- Full investigation trace.

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
