# JudgeResult and TacticianResult

## JudgeResult

The Judge returns structured evidence rather than text alone.

Core fields:

- `schema_version`
- `question`
- `answer`
- `status`
- `origin`
- `confidence`
- `authority`
- `intent`
- `cards`
- `rules`
- `rulings`
- `retrieval_queries`
- `assumptions`
- `warnings`
- `source_versions`
- `source_health`
- `validation_attempts`
- `reviewed_by`
- `review_challenges`
- `authority_trace`
- `llm_called`
- `timings`

## TacticianResult

TacticianResult keeps the Judge-compatible evidence fields and adds strategic structure:

- `strategy_intent`
- `synergies`
- `risks`
- `combo_classification`
- `combo_steps`
- `outcomes`
- `inherited_cards`
- `judge_queries`
- nested `judge_result`

The nested Judge package preserves factual provenance even when the final answer is strategic.
