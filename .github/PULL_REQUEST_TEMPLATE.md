## Summary

Describe what changed and why.

## Scope

- [ ] Application behavior
- [ ] Judge or factual authority
- [ ] Strategist behavior
- [ ] Source or retrieval logic
- [ ] API or UI contract
- [ ] Tests or quality infrastructure
- [ ] Documentation or repository health

## Source-grounding impact

Explain whether this change affects Oracle, rules, rulings, legality, source provenance, or the Judge–Strategist authority boundary.

## Validation

List the commands and campaigns executed.

```text
python scripts/ci_check.py
```

- [ ] Focused tests pass
- [ ] `git diff --check` passes
- [ ] No large generated sources, reports, databases, logs, or secrets were added
- [ ] New behavior has a regression test
- [ ] Markdown documentation is written in English

## Known limitations

Document anything that was not tested or remains intentionally out of scope.
