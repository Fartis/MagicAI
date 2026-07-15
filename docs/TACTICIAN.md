# Tactician profile

The internal profile name is `Tactician`; the local UI displays **Estratega**.

## Responsibility

The Tactician analyzes:

- combos and loops;
- synergies;
- game lines and sequencing;
- deck construction and upgrades;
- risks, interaction points, and alternatives;
- format, bracket, budget, collection, and local-metagame constraints.

It does not open Oracle, rules, rulings, Commander Spellbook, EDHREC, or user collection files directly. It asks the Judge-owned source gateway for structured evidence.

## Current milestone: 0.2

Implemented:

- automatic handoff from `POST /ask`;
- explicit `POST /tactician/ask`;
- strategic intent classification;
- previous-turn card inheritance;
- structured `strategy_intent`, `combo_classification`, `combo_steps`, and `outcomes`;
- generic recognition of a three-piece loop consisting of:
  - a creature with Undying;
  - a sacrifice outlet that generates mana;
  - an ability that removes the +1/+1 counter and creates a token;
- Judge review challenges for contradictory LLM answers;
- Judge capability registry.

## Evidence loop

Target design:

```text
Tactician forms a hypothesis
  → asks the Judge for evidence
  → checks gaps and contradictions
  → asks follow-up questions
  → constructs a line
  → Judge validates every factual claim
  → Critic attempts to break the result
  → publish or declare uncertainty
```

The current implementation records a first `judge_queries` trace. Multi-query planning is the next milestone.

## Constraints

User-provided format, Commander bracket, budget, collection, or preferences constrain the recommendation. They do not change Oracle text or rules.
