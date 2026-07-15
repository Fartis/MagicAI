# MagicAI developer campaign commands

This document covers long evaluation runs. Evaluation artifacts do not train models, modify weights, or promote cases automatically.

## Recommended campaign layout

```bash
CAMPAIGN="oracle-exhaustive"
OUTPUT="quality-results/${CAMPAIGN}"
LOG="logs/${CAMPAIGN}.log"
PIDFILE="logs/${CAMPAIGN}.pid"
mkdir -p "$OUTPUT" logs
```

## Background execution

```bash
nohup env PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir "$OUTPUT" \
  > "$LOG" 2>&1 &
echo $! | tee "$PIDFILE"
```

## Monitor

```bash
tail -f "$LOG"
```

```bash
PID=$(cat "$PIDFILE")
kill -0 "$PID" 2>/dev/null && echo running || echo stopped
```

## Resume

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir "$OUTPUT" \
  --resume
```

## Package results

```bash
tar -czf "${CAMPAIGN}.tar.gz" "$OUTPUT" "$LOG"
sha256sum "${CAMPAIGN}.tar.gz" > "${CAMPAIGN}.tar.gz.sha256"
```

## Worker policy

Use bounded parallelism. Start with four workers and reduce the value if the machine becomes memory-bound. Do not launch every shard simultaneously.

## Interpretation

A harness PASS is not factual authority. Review premise validity, semantic contracts, evidence sufficiency, routing origin, and LLM-call counts.
