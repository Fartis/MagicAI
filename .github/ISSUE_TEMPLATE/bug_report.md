---
name: Bug report / Informe de error
about: Report a reproducible MagicAI problem
labels: bug
---

## Summary / Resumen

Describe what happened and why it is incorrect.

## Area / Área

- [ ] Card selection / Selección de carta
- [ ] Rule retrieval / Recuperación de reglas
- [ ] Renderer
- [ ] Validation / Validación
- [ ] Conversation / Conversación
- [ ] API
- [ ] Dynamic Gauntlet or campaign
- [ ] Documentation
- [ ] Other / Otro

## Question or scenario / Pregunta o escenario

```text
Paste the exact question.
```

## Actual result / Resultado actual

```text
Paste the answer, traceback or report excerpt.
```

## Expected result / Resultado esperado

Explain the correct behavior and, when possible, the supporting Oracle text or rule.

## Reproduction / Reproducción

```bash
# Exact command, seed or replay command
```

Include when available:

- seed;
- concept and template;
- manifest entry;
- failure JSON;
- card name and Oracle evidence;
- rules source version;
- model and Ollama version.

## Failure classification / Clasificación

- [ ] False premise
- [ ] Selector failure
- [ ] Retrieval failure
- [ ] Routing failure
- [ ] Renderer failure
- [ ] Validator failure
- [ ] Contract mismatch
- [ ] LLM generation issue
- [ ] Unknown

## Environment / Entorno

```text
OS:
Python:
MagicAI commit:
Model:
Ollama:
```

## Additional context / Contexto adicional

Do not attach Scryfall bulk files, local databases or private conversations.
