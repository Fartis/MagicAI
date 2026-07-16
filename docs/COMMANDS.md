# MagicAI command reference

## Environment

```bash
cd ~/MagicAI
source .venv/bin/activate
export PYTHONPATH=.
```

## Start API and UI

```bash
python -m uvicorn magicai.api:app --reload
```

## Source updates

```bash
./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py
```

## Focused tests

```bash
python -m tests.validation.rule_renderer_test
python -m tests.validation.oracle_renderer_test
python -m tests.validation.answer_validation_test
python -m tests.tactician.tactician_reviewer_test
python -m tests.tactician.tactician_strategy_test
python -m tests.tactician.tactician_conversation_handoff_test
python -m tests.tactician.tactician_input_reasoning_test
python -m tests.tactician.tactician_followup_reasoning_test
python -m tests.conversation.tactician_strategy_context_test
python -m tests.api.tactician_api_contract_test
```

## Fast pull request checks

```bash
python scripts/ci_check.py
```

## Release packages

```bash
python scripts/package_release.py --source
python scripts/package_release.py --full
```

## GitHub repository analysis export

```bash
./scripts/export_github_analysis.sh
```

## Dynamic Gauntlet

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 42
```

## Multi-seed campaign

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 184729 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/dynamic-campaign \
  --require-full-coverage
```

Resume:

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 184729 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/dynamic-campaign \
  --require-full-coverage \
  --resume
```

## Exhaustive Oracle audit

```bash
python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir quality-results/oracle-exhaustive
```

## Git checks

```bash
git status --short
git diff --check
git diff --stat
```

## Judge Tool Gateway

Inspect capabilities:

```bash
curl -s http://127.0.0.1:8000/meta | python -m json.tool
```

Resolve Oracle evidence:

```bash
curl -s -X POST http://127.0.0.1:8000/judge/tools/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "oracle_lookup",
    "arguments": {"card_names": ["Young Wolf"]},
    "purpose": "manual_gateway_check"
  }' | python -m json.tool
```

Resolve rules:

```bash
curl -s -X POST http://127.0.0.1:8000/judge/tools/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "rules_lookup",
    "arguments": {"identifiers": ["702.93", "701.21", "700.4"]},
    "purpose": "verify_undying_sacrifice"
  }' | python -m json.tool
```

## Tactician conversational understanding

Run the focused orchestration checks:

```bash
python -m tests.tactician.tactician_response_orchestration_test
python -m tests.tactician.tactician_input_reasoning_test
python -m tests.tactician.tactician_followup_reasoning_test
```

Run the deterministic 40-scenario conversation gauntlet:

```bash
python -m tests.quality.tactician_conversations.runner \
  --mode fixture \
  --cases tests/quality/cases/tactician_conversations \
  --output-dir quality-results/tactician-conversations
```

Run the contract and CI regression wrappers:

```bash
python -m tests.quality.tactician_conversation_contract_test
python -m tests.quality.tactician_conversation_regression_test
```

Run the same cases against the local MagicAI installation:

```bash
python -m tests.quality.tactician_conversations.runner \
  --mode local \
  --cases tests/quality/cases/tactician_conversations \
  --output-dir quality-results/tactician-conversations-local
```

Promote an exported result into a review-only candidate:

```bash
python scripts/promote_tactician_feedback.py exported-result.json
```

Candidates are not added to the active regression corpus automatically.
