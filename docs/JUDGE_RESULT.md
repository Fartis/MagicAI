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

Los clientes existentes pueden seguir leyéndolos. Los campos nuevos son aditivos. `schema_version` identifica la política de compatibilidad del contrato.

## Campos

```json
{
  "schema_version": "1.0",
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
  "source_health": {
    "status": "ready",
    "ready": true,
    "complete": true,
    "sources": {}
  },
  "validation_attempts": 0
}
```

### `schema_version`

La versión inicial pública es `1.0`. Dentro de `1.x` no se eliminarán ni renombrarán campos existentes; pueden añadirse campos opcionales. Consulta [API_CONTRACT.md](API_CONTRACT.md).

### `status`

- `answered`: el Juez ofrece una respuesta factual.
- `needs_clarification`: hay varias interpretaciones compatibles y el usuario debe elegir.
- `insufficient_evidence`: las fuentes recuperadas no permiten una respuesta completa segura.
- `strategy_required`: la parte factual está disponible, pero la recomendación pertenece a Deck Master.
- `false_premise`: el Juez detectó y corrigió una premisa falsa de alta confianza antes de responder.

### `origin`

- `disambiguation`
- `deterministic_rule`
- `deterministic_oracle`
- `strategy_boundary`
- `llm_validated`
- `safe_fallback`
- `premise_guard`

### `confidence`

- `high`: respuesta determinista, desambiguación o frontera de autoridad.
- `medium`: respuesta del LLM aceptada por el validador o fallback Oracle completo.
- `low`: evidencia insuficiente o fallback incompleto.

La confianza describe la ruta de producción y validación; no es una probabilidad matemática.

## Evidencia

`cards` expone el Oracle local recuperado, `rules` identifica las reglas utilizadas y `rulings` contiene aclaraciones oficiales recuperadas del bulk local de Scryfall cuando la pregunta las solicita explícitamente. El Juez no consulta la red durante una respuesta.

`source_versions` solo publica versiones que pueden establecerse honestamente desde archivos locales. Para Comprehensive Rules se usa la fecha efectiva del documento. Para los bulk de Scryfall se publica, cuando existe, la marca temporal del archivo y se etiqueta expresamente como `file_mtime`.

`source_health` expone si Oracle y Comprehensive Rules están disponibles y si las fuentes opcionales —símbolos y rulings— están completas. No sustituye al endpoint `/health`, que también comprueba Ollama.

## Compatibilidad interna

- `MagicAI.ask()` continúa devolviendo solo texto.
- `MagicAI.ask_result()` devuelve `JudgeResult`.
- La API utiliza `ask_result()`.
- Open Judge registra `status`, `origin`, `confidence` y `authority` en sus informes.

## Implementado en 10.15b

- rulings oficiales desde un bulk local indexado por `oracle_id`;
- supuestos conservadores derivados de condiciones explícitas de la respuesta;
- corrección de premisas falsas de alta confianza mediante `premise_guard`;

## Implementado en 10.15c

- versión pública `schema_version=1.0`;
- política de compatibilidad aditiva;
- salud de fuentes en `JudgeResult` y `GET /health`;
- metadata del contrato en `GET /meta`;
- errores HTTP estructurados;
- puerta de estabilidad para tres baselines Open Judge.

## Pendiente

- validar tres baselines consecutivas en la máquina objetivo;
- cerrar el Judge Release Candidate y congelar el contrato durante la primera UI beta.
