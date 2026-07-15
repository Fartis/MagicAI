# Tactician input reasoning

Sprint 12.2b adds a structured reasoning layer between the user's message and strategic synthesis.

## Goal

The Tactician must not treat the Judge's prose as the answer. It first analyzes what the player is asserting, asking, correcting, or challenging, then requests the evidence needed to evaluate those claims.

## Pipeline

```text
user input
  → speech-act and intent analysis
  → claim extraction
  → bounded investigation plan
  → Judge Tool Gateway calls
  → claim verdicts
  → conversational strategic synthesis
  → evidence verification metadata
```

## Input analysis

The analyzer records:

- language;
- speech act such as question, hypothesis, challenge, or follow-up;
- strategic intent;
- causal markers;
- detected concepts;
- structured claims.

The result is auditable metadata, not a hidden chain-of-thought transcript.

## Claim verdicts

Each extracted claim can be classified as:

- `supported`
- `contradicted`
- `partially_supported`
- `insufficient_evidence`
- `strategic_opinion`

A verdict records a concise explanation and the source identifiers that support it.

## Current deterministic interaction family

The first full reasoning family covers:

- Young Wolf;
- Carrion Feeder;
- The Ozolith;
- Undying;
- counters across zone changes;
- leaves-the-battlefield timing;
- last known information.

The Tactician correctly explains that The Ozolith does not remove Young Wolf's +1/+1 counter before Undying checks the creature's last battlefield state.

## Strategic follow-ups

The active strategic context now supports follow-up intents such as:

- `play_sequence`
- `combo_disruption`
- `combo_requirements`
- `interaction_hypothesis`

The first supported sequence family covers Young Wolf, Ashnod's Altar, and Ghave, Guru of Spores.

## Limits

This milestone is not a universal natural-language theorem prover. Claim extraction and verdict generation are deterministic and intentionally narrow. Sprint 12.3 will generalize investigation planning, evidence sufficiency, alternatives, and counterexample search.
