# Tactician input reasoning and response orchestration

Sprint 12.3a extends the structured reasoning layer with explicit hypotheses, evidence-sufficiency scoring, bounded reactive searches, response ownership, and factual-core preservation.

## Goal

The Tactician must answer the current question rather than merely mentioning the active cards or repeating a generic combo classification. It must decide whether the current turn is primarily factual, strategic, or mixed, then preserve the appropriate authority boundary.

## Pipeline

```text
user wording
  → shared casual-language normalization
  → session language policy
  → speech-act and intent analysis
  → claim and question-target extraction
  → hypothesis decomposition and evidence requirements
  → bounded Judge Tool Gateway investigation
  → sufficiency scoring and reactive fallback search
  → claim verdicts
  → response-mode arbitration
  → factual-core extraction
  → Judge-led, Tactician-led, or hybrid synthesis
  → factual-core coverage validation
  → answer-obligation validation
  → evidence verification metadata
```

## Response modes

### `judge_led`

Used for rules and mechanic questions such as:

```text
What happens if I sacrifice Young Wolf?
What does dying mean?
When is the counter condition checked?
```

The Judge owns the factual core. The Tactician may adapt tone and connect the answer to the conversation, but it may not replace the rules explanation with a generic strategic summary.

### `tactician_led`

Used for strategic questions such as:

```text
Do these cards form a combo?
What order should I use?
Where can opponents interrupt the loop?
```

The Tactician synthesizes the line from Judge-owned evidence.

### `hybrid`

Used when a rules result must be connected to a strategic conclusion, for example explaining exactly why a proposed combo fails.

## Factual core

On a `judge_led` turn, the factual core is extracted from the Judge's validated answer sentence by sentence. This deliberately avoids adding production fixes for individual cards: the preservation rule applies equally to any direct rules answer. If Tactician wording drops a required Judge proposition, orchestration falls back to the validated Judge answer rather than replacing it with a generic strategic summary.

Card-specific expectations belong in the regression corpus, where they test behavior without becoming application routing rules.

The result exposes:

- `factual_core`;
- `factual_core_coverage`;
- `factual_core_preserved`.

A response cannot be marked complete when a required proposition is missing.

## Language policy

Card names and rules keywords are often English even inside a Spanish sentence. They are treated as neutral MTG terms instead of strong language evidence.

Resolution order:

```text
clear current-turn language
  → established session language
  → configured default language
```

The selected language applies to the answer and all user-visible strategic metadata.

## Casual-language normalization

The Judge and Tactician share a conservative normalizer. It converts colloquial wording into retrieval-friendly wording without answering the question or silently correcting its premise.

Examples:

```text
"pisa cementerio" → "is put into a graveyard"
"pisa mesa"       → "enters the battlefield"
"se puede cortar" → "can be responded to or interrupted"
```

The Judge answers in a stable professional register. The Tactician may remain warmer and more conversational.

## Conversation Gauntlet

The initial corpus is stored under:

```text
tests/quality/cases/tactician_conversations/
```

It contains 40 scenarios and 58 turns across:

- direct mechanic resolutions;
- casual and mixed-language wording;
- incorrect interaction hypotheses;
- Young Wolf, Carrion Feeder, and The Ozolith;
- Young Wolf, Ashnod's Altar, and Ghave;
- sequencing, requirements, and disruption follow-ups;
- drift resistance when the Judge prose is not relevant.

Fixture mode is fast and deterministic:

```bash
python -m tests.quality.tactician_conversations.runner \
  --mode fixture \
  --cases tests/quality/cases/tactician_conversations
```

Local mode uses the installed MagicAI sources and model:

```bash
python -m tests.quality.tactician_conversations.runner \
  --mode local \
  --cases tests/quality/cases/tactician_conversations \
  --output-dir quality-results/tactician-conversations-local
```

Both modes generate `summary.json` and `report.html`.

## Feedback promotion

An exported UI result can be converted into a reviewable candidate:

```bash
python scripts/promote_tactician_feedback.py exported-result.json
```

The command never modifies the active regression corpus automatically. A human must add semantic and negative expectations before promotion.

## Autonomous investigation trace

Sprint 12.3a exposes a structured, non-chain-of-thought audit record. Each hypothesis lists its required evidence, resolved and missing evidence, sufficiency score, and whether a fallback search was attempted. Each step records its phase, request, affected hypotheses, score change, result status, and budget state.

The trace is intended for diagnostics, regression tests, and UI inspection. It does not expose private model reasoning.

## Limits

This milestone is not a universal natural-language theorem prover. Hypothesis templates and follow-up policies remain deterministic and intentionally bounded. Sprint 12.3b will add contradiction-aware comparison, dynamic hypothesis expansion, and broader interaction families.


## Land-type layer regression

The manual Blood Moon, Urborg, and Dryad test exposed a false-positive
sufficiency state: Oracle verification alone was scored as complete even though
the user explicitly asked for layer, dependency, timestamp, land-type, and mana
conclusions. Sprint 12.3a1 corrects this by deriving those concepts from the
question and attaching the complete rules package to the answer-basis
hypothesis.

Investigation sufficiency and Judge verification are deliberately separate.
A complete set of lookup results does not make an incomplete Judge answer
verified. `judge_verified` now also requires a non-insufficient Judge status,
and Judge-led answers need either a preserved factual core or a recognized
source-grounded semantic fallback.

## Deterministic answer metadata

Sprint 12.3a2 aligns the public metadata with the actual Judge result. When a
source-grounded deterministic answer satisfies every obligation and the planned
evidence is complete, the Tactician reports the answer as complete and verified,
propagates high confidence, and records `judge:evidence_verification`. An
insufficient Judge result continues to fail closed even if the lookup plan itself
found every requested source.
