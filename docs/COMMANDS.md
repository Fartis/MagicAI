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
python -m tests.api.tactician_api_contract_test
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
