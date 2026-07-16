# Tactician input reasoning

Sprint 12.2c extends the structured reasoning layer introduced in Sprint 12.2b. The Tactician must understand the user's current question, preserve the conversation language, request the relevant rules evidence, and prove that its final answer satisfies the question it was asked.

## Goal

The Tactician must not treat the Judge's prose as the answer. It analyzes what the player is asserting, asking, correcting, or challenging, then requests the evidence needed to evaluate those claims. A completed response must also satisfy an explicit answer contract.

## Pipeline

```text
user wording
  → shared casual-language normalization
  → session language policy
  → speech-act and intent analysis
  → claim and question-target extraction
  → bounded investigation plan
  → Judge Tool Gateway calls
  → claim verdicts
  → conversational strategic synthesis
  → answer-obligation validation
  → evidence verification metadata
```

## Language policy

Card names and rules keywords are often English even inside a Spanish sentence. They are treated as neutral MTG terms instead of strong language evidence.

Resolution order:

```text
clear current-turn language
  → established session language
  → configured default language
```

The selected language applies to the answer and to user-visible strategic metadata such as risks, outcomes, claim explanations, and reasoning summaries.

## Casual-language normalization

The Judge and Tactician share a conservative normalizer. It converts colloquial wording into retrieval-friendly wording without answering the question or silently correcting its premise.

Examples:

```text
"pisa cementerio" → "is put into a graveyard"
"pisa mesa"       → "enters the battlefield"
"se puede cortar" → "can be responded to or interrupted"
```

The Judge still answers in a stable, professional register. The Tactician may remain warmer and more conversational.

## Input analysis

The analyzer records:

- response language and language-policy decision;
- user register;
- canonical retrieval question;
- speech act such as question, hypothesis, challenge, or follow-up;
- strategic or rules-oriented intent;
- question target and answer focus;
- causal markers;
- detected concepts;
- structured claims.

The result is auditable metadata, not a hidden chain-of-thought transcript.

## Rules-oriented intents

Sprint 12.2c adds:

- `rules_clarification`
- `mechanic_definition`
- `mechanic_equivalence`
- `combo_failure_explanation`
- `interaction_timing`

The Tactician owns the conversation, but factual rules claims remain Judge-owned and must be recovered through the Judge Tool Gateway.

## Claim verdicts

Each extracted claim can be classified as:

- `supported`
- `contradicted`
- `partially_supported`
- `insufficient_evidence`
- `strategic_opinion`

A verdict records a concise explanation and the source identifiers that support it. Open questions are not automatically converted into factual claims.

## Answer obligations

Each response receives a small semantic contract. For an Undying terminology question, the required obligations include:

- define `dies`;
- explain that dying and moving from the battlefield to a graveyard are the same event;
- exclude graveyard entry from other zones;
- apply the definition to Undying;
- apply it to the active interaction when relevant.

The response is marked `answer_complete` only when all required checks pass and forbidden drift is absent.

## Current deterministic interaction family

The primary regression covers:

- Young Wolf;
- Carrion Feeder;
- The Ozolith;
- Undying;
- counters across zone changes;
- leaves-the-battlefield timing;
- last known information;
- casual follow-up wording about dying and entering a graveyard.

The Tactician explains that The Ozolith does not remove Young Wolf's +1/+1 counter before Undying checks the creature's last battlefield state.

## Conversation regression seed

The first multi-turn scenario is stored under:

```text
tests/quality/cases/tactician_conversations/sprint12_2c.json
```

It verifies language, intent, required rules, semantic requirements, forbidden drift, answer completeness, and evidence verification. This is the seed for the wider Tactician Conversation Gauntlet planned for Sprint 12.2d.

## Limits

This milestone is not a universal natural-language theorem prover. Normalization, claim extraction, semantic checks, and verdict generation remain deterministic and intentionally bounded. Sprint 12.2d will broaden multi-turn scenario execution and reporting; Sprint 12.3 will generalize autonomous investigation planning.
