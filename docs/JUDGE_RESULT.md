# JudgeResult

`JudgeResult` es el contrato estructurado entre el Juez, la API, la futura UI y los perfiles estratégicos. Mantiene la respuesta textual, pero añade trazabilidad suficiente para saber cómo se obtuvo y qué evidencia la respalda.

## Compatibilidad

`POST /ask` conserva estos campos:

```json
{
  "answer": "...",
  "session_id": "..."
}
```

Los clientes existentes pueden seguir leyendolos. Los campos nuevos son aditivos.

## Campos

```json
{
  "question": "¿Puedo responder durante la resolución?",
  "answer": "No. Ningún jugador recibe prioridad mientras se resuelve...",
  "session_id": "...",
  "status": "answered",
  "origin": "deterministic_rule",
  "confidence": "high",
  "authority": "judge",
  "intent": "rules",
  "cards": [],
  "rules": [
    {
      "number": "117.2e",
      "title": "No player has priority while a spell or ability is resolving."
    }
  ],
  "rulings": [],
  "retrieval_queries": ["priority during resolution"],
  "assumptions": [],
  "warnings": [],
  "source_versions": {
    "comprehensive_rules": "2026-06-19"
  },
  "validation_attempts": 0
}
```

### `status`

- `answered`: el Juez ofrece una respuesta factual.
- `needs_clarification`: hay varias interpretaciones compatibles y el usuario debe elegir.
- `insufficient_evidence`: las fuentes recuperadas no permiten una respuesta completa segura.
- `strategy_required`: la parte factual está disponible, pero la recomendación pertenece a Deck Master.
- `false_premise`: reservado para premisas falsas detectadas explícitamente.

### `origin`

- `disambiguation`
- `deterministic_rule`
- `deterministic_oracle`
- `strategy_boundary`
- `llm_validated`
- `safe_fallback`

### `confidence`

- `high`: respuesta determinista, desambiguación o frontera de autoridad.
- `medium`: respuesta del LLM aceptada por el validador o fallback Oracle completo.
- `low`: evidencia insuficiente o fallback incompleto.

La confianza describe la ruta de producción y validación; no es una probabilidad matemática.

## Evidencia

`cards` expone el Oracle local recuperado y `rules` identifica las reglas utilizadas. `rulings` forma parte del contrato estable, pero permanecerá vacío hasta que el pipeline de rulings esté integrado.

`source_versions` solo publica versiones que pueden establecerse honestamente desde archivos locales. Para Comprehensive Rules se usa la fecha efectiva del documento. Para los bulk de Scryfall se publica, cuando existe, la marca temporal del archivo y se etiqueta expresamente como `file_mtime`.

## Compatibilidad interna

- `MagicAI.ask()` continúa devolviendo solo texto.
- `MagicAI.ask_result()` devuelve `JudgeResult`.
- La API utiliza `ask_result()`.
- Open Judge registra `status`, `origin`, `confidence` y `authority` en sus informes.

## Pendiente

- poblar rulings oficiales;
- emitir supuestos explícitos;
- activar `false_premise`;
- añadir pruebas HTTP completas del contrato;
- fijar política de versionado antes de la UI beta.
