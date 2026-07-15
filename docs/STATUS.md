# Current MagicAI status

> Current release: `v0.1.1-beta` — **Force of Will**
> Next beta milestone: `v0.2.0-beta` — **Ponder**
> Planned 1.0 codename: **NicolAI Bolas**

## Overall assessment

MagicAI is an early public beta with an advanced Judge core and an integrated Tactician foundation.

Approximate maturity relative to the complete vision:

| Area | Maturity |
|---|---:|
| Local Oracle, rules, rulings, and source health | 85% |
| Evidence retrieval and provenance | 75% |
| Deterministic Judge coverage | 70% |
| LLM validation and repair | 50% |
| Evaluation infrastructure | 80% |
| Local UI and persistent history | 65% |
| Tactician handoff and continuity | 35% |
| Formal combo engine | 20% |
| Full deck analysis | 5% |
| Commander Spellbook | 0% |
| Authorized statistics | 0% |

These are planning estimates, not coverage statistics.

## Current strengths

- The model is not the sole authority.
- Sources are local and versioned.
- Deterministic routes avoid unnecessary LLM calls.
- Evaluation campaigns are reproducible and resumable.
- Human audit can expose false positives after harness PASS results.
- Problems are fixed by semantic families rather than card-name exceptions.
- Strategic questions can now hand off automatically to the Tactician.
- Follow-up card context can survive the handoff.

## Current blockers before Ponder

- Multi-query autonomous Tactician planning is not implemented yet.
- The Judge tool gateway is a registry, not yet a complete typed execution API.
- Arbitrary combos are not formally proven through a general state graph.
- Validation can still miss unsupported LLM interpretations outside covered contracts.
- Spellbook, authorized statistics, user collection, and metagame sources are not connected.
- The full exhaustive evaluation must be run on the user's local Oracle snapshot after each major semantic change.


## Repository health

The first repository-health foundation adds fast pull request CI, clean release packaging, community policies, dependency update configuration, and explicit branching and release documentation. Large Oracle and Ollama campaigns remain separate from fast CI.
