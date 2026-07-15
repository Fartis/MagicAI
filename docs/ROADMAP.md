# MagicAI roadmap

## Release targets

### 0.1 beta — Ponder

The first integrated beta requires:

- reliable Judge answers for the covered families;
- source-grounded validation and safe failure;
- automatic Judge-to-Tactician handoff;
- resilient conversation continuity;
- iterative Tactician queries through the Judge tool gateway;
- formal combo reconstruction;
- useful local UI and persistent history;
- reproducible installation and evaluation.

### 1.0 — NicolAI Bolas

The first major release should add mature deck analysis, authorized strategic sources, collection awareness, broader format support, and production-grade packaging.

## Sprint 12 — Tactician integration

### 12.0 — Initial vertical slice — complete

- Tactician profile and API endpoint.
- Judge contradiction review.
- Basic role and synergy analysis.

### 12.1 — Automatic handoff and continuity — implemented

- Automatic handoff from `/ask`.
- No duplicate conversation turns.
- Referential previous-card inheritance.
- Intent-specific combo boundary.
- Structured combo steps and outcomes.
- Generic Young Wolf + mana outlet + counter converter loop recognition.
- Judge capability registry.

### 12.2 — Judge tool gateway

- Typed tool requests and responses.
- Per-tool provenance, version, latency, and authority.
- Legality exposed to Tactician evidence.
- Query cache and budgets.
- Capability-missing responses.

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
