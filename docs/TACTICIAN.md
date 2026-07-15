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

It does not open Oracle, rules, rulings, Commander Spellbook, EDHREC, or user collection files directly. It requests structured evidence through the Judge Tool Gateway.

## Current milestone: 0.3

Implemented:

- automatic handoff from `POST /ask`;
- explicit `POST /tactician/ask`;
- strategic intent classification;
- previous-turn card inheritance;
- structured `strategy_intent`, `combo_classification`, `combo_steps`, and `outcomes`;
- generic recognition of a three-piece Undying loop;
- Judge review challenges for contradictory LLM answers;
- executable, typed Judge Tool Gateway;
- bounded Oracle refresh through the Judge before strategic synthesis;
- tool-call provenance in `judge_tool_calls` and `judge_queries`;
- explicit `tactician_synthesized` metadata.

## Evidence loop

Target design:

```text
Tactician forms a hypothesis
  → requests one or more Judge tools
  → checks gaps and contradictions
  → requests narrower evidence
  → constructs a line
  → Judge validates factual claims
  → Critic attempts to break the result
  → publish or declare uncertainty
```

Milestone 0.3 provides the executable gateway and a first bounded Oracle refresh. Autonomous multi-query planning remains the next milestone.

## Personality

The Judge should remain formal and concise. The Tactician should be warmer, conversational, and proactive while preserving the same factual boundary.

It should:

- explain why a line is attractive;
- mention risks and interaction windows;
- infer likely follow-up meaning from active strategic context;
- ask a question only when missing information materially changes the recommendation;
- never invent card text or rules to sound helpful.

## Constraints

User-provided format, Commander bracket, budget, collection, or preferences constrain the recommendation. They do not change Oracle text or rules.
