# Community Feedback Gauntlet

El Community Feedback Gauntlet permite introducir escenarios de reglas individuales, seleccionados manualmente y parafraseados, sin rastrear, copiar ni republicar un foro.

Su función es **evaluar el código del Juez**, no enseñar al modelo. Las campañas no hacen fine-tuning, no generan archivos de entrenamiento, no modifican pesos y no promocionan casos automáticamente.

```text
caso exploratorio
→ ejecución local del Juez
→ REVIEW_REQUIRED + JudgeResult
→ revisión humana contra fuentes actuales
→ diagnóstico de una causa genérica
→ cambio de código
→ contrato semántico validado
→ regresión permanente
```

## Frontera de autoridad

El contenido comunitario nunca se considera autoridad factual. Solo aporta el escenario y, opcionalmente, contexto histórico. Las Comprehensive Rules, Oracle y rulings actuales siguen siendo la autoridad.

No incluyas:

- nombres de usuario o información de perfil;
- publicaciones o comentarios completos;
- respuestas literales del foro;
- datos personales;
- exportaciones masivas sin permiso.

Utiliza una paráfrasis breve de la pregunta reglamentaria.

## Contrato de solo evaluación

Las plantillas y exportaciones de la UI incluyen:

```json
{
  "artifact_purpose": "evaluation",
  "training_allowed": false,
  "automatic_learning": false,
  "automatic_promotion": false
}
```

El cargador rechaza un propósito distinto, cualquier bandera activada y campos inequívocamente destinados a entrenamiento, como `assistant_target`, `training_target`, `target_completion` o `fine_tune_messages`.

## 1. Crear un caso

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --create-template community_feedback/inbox/mi_caso.json
```

También puede generarse desde la UI con **Crear caso Gauntlet**. Esa exportación conserva únicamente los turnos del usuario; no inserta la respuesta del asistente ni el `JudgeResult` como objetivo que el modelo deba imitar.

Edita el JSON generado. `community_feedback/inbox/` está ignorado por Git para evitar que borradores locales y referencias se publiquen accidentalmente.

Para un escenario inspirado en un foro, conserva solo procedencia mínima:

```json
{
  "platform": "reddit",
  "url": "enlace opcional",
  "topic_id": "identificador opcional",
  "paraphrased": true,
  "contains_verbatim_quote": false,
  "contains_personal_data": false
}
```

El cargador rechaza casos que declaren texto literal, datos personales o campos como `username`, `author`, `raw_post` o `comment_text`.

## 2. Ejecutar una campaña

Una campaña con identificador estable puede contener uno, cientos o miles de casos:

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --checkpoint-every 25
```

Cada caso se escribe inmediatamente mediante reemplazo atómico. `--checkpoint-every` controla cada cuántos casos se regeneran los resúmenes agregados, no la persistencia del resultado individual.

Los casos exploratorios siempre producen:

```text
REVIEW_REQUIRED
```

Nunca reciben un falso `PASS` por carecer todavía de contrato semántico.

### Reanudar después de apagar o interrumpir el PC

Ejecuta la misma selección y el mismo identificador:

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --resume
```

Los casos ya completados no vuelven a ejecutarse. El manifiesto guarda una huella SHA-256 de cada definición y rechaza mezclar en la misma campaña un caso que haya sido editado. Si cambias preguntas o contratos, crea otro `campaign-id`.

Para reintentar únicamente los casos que terminaron con excepción:

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --resume \
  --retry-errors
```

Por defecto se calculan hashes de Comprehensive Rules, Oracle, rulings y symbology cuando están presentes. Para una comprobación rápida que solo registre rutas y tamaños:

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id smoke-eval-001 \
  --skip-source-hashes
```

## 3. Salida de campaña

```text
resultado_community_feedback/judge-eval-001/
├── campaign_manifest.json
├── campaign_progress.json
├── community_feedback_summary.json
├── community_feedback_summary.md
├── community_feedback_summary.html
├── findings_by_family.json
├── replay_commands.txt
├── completed/
├── execution_errors/
└── review_packets/
```

`campaign_manifest.json` registra, entre otros datos:

- commit y rama Git cuando están disponibles;
- estado limpio o modificado del árbol;
- modelo, temperatura cero y URL local de Ollama;
- versión de Python y plataforma;
- hashes, tamaño y presencia de las fuentes locales;
- huellas de los casos;
- progreso, errores y tiempo acumulado.

`findings_by_family.json` agrupa diagnósticos como:

```text
CARD_EXTRACTION_FAILURE
RULE_INTENT_FAILURE
ORACLE_RETRIEVAL_FAILURE
RULE_RETRIEVAL_FAILURE
CONTEXT_FAILURE
RENDERER_FAILURE
VALIDATOR_FAILURE
FACTUAL_CONTRADICTION
HALLUCINATION
UNSUPPORTED_SCENARIO
EXECUTION_ERROR
REVIEW_REQUIRED
```

La clasificación automática es una ayuda para priorizar. La familia definitiva y la solución genérica se confirman durante la revisión humana.

Los paquetes de `review_packets/` conservan la pregunta parafraseada, la respuesta, el `JudgeResult`, el estado conversacional y el bloque de decisión. Las ediciones humanas de `review_decision` se preservan cuando una campaña reanudada regenera los informes.

No se crean archivos como:

```text
training.jsonl
fine_tuning_dataset.json
prompt_completion.jsonl
learned_examples.json
```

## 4. Revisar y promover

Tras comprobar el escenario contra fuentes oficiales actuales, cambia:

```json
"mode": "validated"
```

y registra:

```json
"review": {
  "status": "current_rules_validated",
  "rules_version": "AAAA-MM-DD",
  "validated_at": "AAAA-MM-DD",
  "expected_summary": "Respuesta actual resumida"
}
```

Cada turno puede definir el mismo contrato semántico utilizado por Open Judge:

```json
{
  "required_all": [
    "habilidad original"
  ],
  "required_any": [
    [
      "permanece en la pila",
      "existe independientemente de su fuente"
    ]
  ],
  "forbidden": [
    {
      "text": "la habilidad original desaparece",
      "outcome": "FACTUAL_CONTRADICTION"
    }
  ],
  "success_outcome": "PASS",
  "missing_outcome": "CONTEXT_FAILURE"
}
```

Ejecuta casos validados con un nuevo identificador:

```bash
PYTHONPATH=. python -m tests.quality.community_feedback_test \
  --input ruta/a/casos_validados \
  --campaign-id validated-regression-001 \
  --strict
```

Solo los casos normalizados, parafraseados y revalidados contra fuentes actuales deben promocionarse a tests versionados.

## Flujo recomendado para colaborar

1. Parafrasea una pregunta que haya revelado un posible fallo.
2. Crea y ejecuta un caso exploratorio.
3. Comparte `campaign_manifest.json`, `findings_by_family.json` y los paquetes de revisión relevantes.
4. Revalidamos el escenario contra CR, Oracle y rulings actuales.
5. Confirmamos la familia del fallo.
6. Implementamos una solución genérica, sin condicionales por carta o caso.
7. Ejecutamos generalización y regresiones anteriores.
8. Añadimos el contrato validado como regresión permanente.

Este flujo no autoriza importaciones masivas ni sustituye los permisos que pudieran exigir JudgeApps, Reddit u otra plataforma.
