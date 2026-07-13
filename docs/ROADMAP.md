# 🗺️ Hoja de ruta de MagicAI

> La prioridad actual es finalizar el Juez antes de ampliar el producto con perfiles estratégicos.

[Español](#-estado-de-la-hoja-de-ruta) · [English](#-roadmap-summary)

---

## 🇪🇸 Estado de la hoja de ruta

```text
Fuentes y pipeline base              ✅
Renderizadores y validación          ✅
Gauntlet dinámico                    ✅
Campañas multisemilla                ✅
Filtro de cartas oficiales           ✅
Open Judge Gauntlet                  ✅
JudgeResult estructurado             ✅
Cobertura guiada por fallos          ⏳
Judge Release Candidate              ⏳
UI modular                           ⏳
Deck Master                          ⏳
Deckbuilder                          ⏳
```

---

## Fase 1 — Fundamentos del Juez ✅

Completado:

- arquitectura modular;
- Oracle local;
- Comprehensive Rules locales;
- API REST;
- conversación y desambiguación;
- recuperación de cartas y reglas;
- integración con Ollama;
- validación y fallbacks;
- suites de regresión y rendimiento.

Resultado: MagicAI dejó de depender exclusivamente de la memoria del modelo.

---

## Fase 2 — Hardening determinista ✅

Completado:

- routing de preguntas de reglas;
- renderizadores deterministas;
- queries semánticas y numéricas;
- validación de Oracle y lenguaje;
- Gauntlet fijo;
- Generalization Probe;
- Gauntlet dinámico reproducible;
- replay de fallos;
- escenarios `rules-only`;
- campañas multisemilla;
- auditoría de premisas;
- exclusión de cartas funny, silver-border, acorn y playtest;
- routing de sacrificios pagados como coste y disparos de muerte;
- detección de Commander mediante referencias a la zona de mando;
- cobertura determinista inicial de capas, continuidad y dependencias.

Últimos checkpoints validados:

```text
Dynamic Campaign: 3 seeds · 126/126 PASS · 14 concepts · 42 templates
Matriz completa: 216/216 ejecuciones · 0 WARN · 0 FAIL
```

---

## Sprint 10.14 — Open Judge Gauntlet ✅

Objetivo: medir lo que el Juez ya puede resolver fuera de rutas preparadas y separar errores técnicos de fallos semánticos.

Infraestructura implementada:

- corpus ampliado a 11 conversaciones y 27 turnos;
- contratos semánticos por turno;
- reutilización del mismo corpus por la Regression Suite legacy;
- captura del estado conversacional después de cada respuesta;
- clasificación de fallos por categoría;
- informes TXT, JSON, XML y HTML;
- artefactos JSON individuales para cada turno no satisfactorio;
- modo baseline por defecto y modos estrictos opcionales.

Clasificación disponible:

```text
PASS
CORRECT_BUT_INCOMPLETE
NEEDS_CLARIFICATION
STRATEGY_REQUIRED
INSUFFICIENT_EVIDENCE
FALSE_PREMISE_HANDLED
RETRIEVAL_FAILURE
CONTEXT_FAILURE
FACTUAL_CONTRADICTION
HALLUCINATION
EXECUTION_ERROR
```

Primera baseline fijada el 12 de julio de 2026: 9 conversaciones, 25 turnos y 0 errores de ejecución. Tras 10.14c alcanzó 23/25 PASS; 10.14e amplió el corpus con desambiguación de Squee y resultados estratégicos explícitos; 10.15b añade un caso de premisa falsa y lleva el total a 11 conversaciones y 27 turnos. La revisión manual separó fallos reales del Juez de falsos negativos del evaluador.

La primera ronda cubre especialmente:

- continuidad de una carta entre turnos;
- diferencias entre lanzar y entrar al campo de batalla;
- keyword frente a carta homónima;
- comparación de dos cartas y atribución correcta de habilidades;
- seguimiento de una regla explícita;
- cambio de tema;
- continuidad de procedimientos como London Mulligan;
- Undying con y sin contador +1/+1.

Criterio de cierre del sprint:

- baseline reproducible guardada;
- contratos ajustados tras revisión manual;
- cero errores de ejecución del runner;
- cada fallo relevante clasificado;
- prioridades de hardening ordenadas por familia genérica.

### Sprint 10.14b–e — Hardening guiado por Open Judge 🚧

Hardening acumulado guiado por la baseline:

- estado compartido para cartas, keywords, reglas y búsquedas conceptuales;
- conservación de dos cartas en comparaciones;
- desambiguación contextual entre keyword y carta homónima;
- seguimiento de reglas numeradas y procedimientos;
- reducción de ruido en definiciones directas de keywords;
- respuestas deterministas para definiciones de Undying/Persist y sus diferencias;
- relación genérica entre disparos «when you cast» y preguntas de entrada;
- interpretación genérica de costes «Sacrifice another ...»;
- normalización semántica del evaluador;
- cantidades variables basadas en expresiones Oracle con `X`;
- frontera factual/estratégica mediante `STRATEGY_REQUIRED`;
- exclusión de objetos suplementarios y caso abierto de Squee;
- corrección de la referencia de exilio a la regla 701.13.

Cierre: repetir el Open Judge Gauntlet y comprobar que todos los turnos son `PASS`, `NEEDS_CLARIFICATION` o `STRATEGY_REQUIRED`, sin contradicciones factuales.

---

## Sprint 10.15 — Contrato `JudgeResult` ✅

Crear una salida estructurada estable:

```json
{
  "status": "answered",
  "answer": "...",
  "cards": [],
  "rules": [],
  "rulings": [],
  "assumptions": [],
  "warnings": [],
  "confidence": "high",
  "source_versions": {}
}
```

Primera entrega implementada:

- `MagicAI.ask_result()` y compatibilidad de `MagicAI.ask()`;
- estados `answered`, `needs_clarification`, `insufficient_evidence`, `strategy_required` y `false_premise`;
- origen de respuesta determinista, LLM validado, fallback, estrategia o desambiguación;
- evidencia estructurada de cartas y reglas;
- autoridad, confianza, consultas de recuperación, advertencias y versiones locales de fuentes;
- respuesta `/ask` ampliada sin eliminar `answer` ni `session_id`;
- metadata `JudgeResult` incluida en los informes Open Judge.

Cierre del sprint:

- rulings locales y renderer literal determinista;
- supuestos conservadores y premisas falsas de alta confianza;
- `schema_version=1.0` y política de compatibilidad aditiva;
- endpoints `/meta` y `/health`;
- errores HTTP estructurados;
- puerta para tres baselines Open Judge consecutivas.

Cierre validado:

- tres baselines completas consecutivas e idénticas en la máquina objetivo;
- 27/27 resultados aceptables por ejecución y cero fallos críticos;
- schema `1.0` congelado con política de compatibilidad aditiva para la UI beta.

Pendiente del Release Candidate formal: repetir la matriz controlada completa y los smoke tests finales del entorno objetivo.

---

## Sprints 10.16–10.18 — Cobertura guiada por fallos ⏳

La prioridad se decidirá con el Open Judge Gauntlet, pero las familias candidatas son:

### Lanzamiento y costes

- costes adicionales y alternativos;
- reducciones e incrementos;
- X;
- modos y elecciones;
- objetivos legales.

### Estado y temporalidad

- acciones basadas en estado;
- Last Known Information;
- disparos retrasados;
- cambio de control;
- fichas que dejan de existir.

### Cartas complejas

- transform y double-faced cards;
- modal DFC;
- split, aftermath y Adventure;
- Prototype;
- habilidades concedidas;
- rulings específicos.

### Efectos continuos

- capas;
- timestamps;
- dependencias;
- CDA;
- copias y valores copiables;
- cambios de texto y tipo.

No se creará un renderer para cada regla. Se priorizarán patrones frecuentes, de alto impacto o propensos a alucinación.

---

## Sprint 10.19 — Judge Release Candidate ⏳

Criterios de cierre:

- Open Judge Gauntlet con umbrales definidos;
- campañas dinámicas estables;
- `JudgeResult` documentado;
- estados de aclaración y evidencia insuficiente;
- fuentes versionadas;
- actualización reproducible de Oracle, reglas y símbolos;
- API interna estable;
- documentación y comandos actualizados;
- ausencia de regresiones críticas conocidas.

A partir de este punto, los bugs descubiertos por perfiles posteriores se tratarán como mantenimiento del Juez, no como rediseño arquitectónico.

---

## Fase 3 — UI modular del Juez 🚧

Primera interfaz de usuario real:

- conversación con el Juez;
- historial de sesiones;
- panel de cartas recuperadas;
- reglas y rulings utilizados;
- estado de la respuesta;
- supuestos y advertencias;
- versión de fuentes;
- exportación de consultas.

La UI se diseñará desde el principio para incorporar nuevos perfiles sin rehacer la aplicación.

Inspiración visual: dashboard del Gauntlet actual, adaptado a una experiencia conversacional.

---

## Fase 4 — Deck Master ⏳

Responsabilidad:

- valorar un mazo;
- explicar cómo jugarlo;
- plan de juego por fases;
- mulligans;
- fortalezas y debilidades;
- matchups;
- nivel de potencia y consistencia.

Restricción:

> Para reglas, Oracle, legalidad, identidad de color y funcionamiento de cartas, Deck Master solo podrá consultar al Juez.

---

## Fase 5 — Deckbuilder ⏳

Responsabilidad:

- crear un mazo desde cero;
- mejorar una lista existente;
- proponer paquetes y redundancia;
- ajustar curva, tierras y proporciones;
- respetar presupuesto, formato y nivel objetivo;
- explicar cada cambio.

Restricción:

> Deckbuilder no tendrá acceso factual directo a Internet ni a fuentes de cartas. Sus verificaciones pasarán por el Juez.

En fases posteriores podrá consumir estadísticas o metajuego mediante servicios separados y explícitos, sin convertir esas fuentes en autoridad de reglas.

---

## Fase 6 — Colección, proyectos y enseñanza ⏳

Posibles extensiones:

- colección local del usuario;
- comparación de versiones de un mazo;
- seguimiento de cambios;
- modo enseñanza;
- ejercicios de reglas;
- análisis de partidas;
- exportación a formatos de decklist.

Estas funciones no deben retrasar el cierre del Juez ni debilitar su frontera factual.

---

## 🇬🇧 Roadmap summary

The immediate goal is to finish the Judge. The next milestones are an open-question Gauntlet, a structured `JudgeResult`, coverage driven by observed failures and a Judge Release Candidate.

Only after that will MagicAI ship its modular UI, followed by Deck Master and Deckbuilder. Both strategic profiles will be required to use the Judge as their sole factual authority for rules, Oracle text, rulings and legality.

### Sprint 11.0 — UI beta foundation 🚧

- shell web local servida por FastAPI;
- chat con sesiones;
- panel de evidencia de `JudgeResult 1.0`;
- estado de fuentes y Ollama;
- tratamiento visual de aclaración, estrategia, premisas falsas y evidencia insuficiente;
- persistencia visual en `localStorage`;
- layout responsive y accesible.

Criterio de cierre:

- `/ui` se sirve sin recursos externos;
- el flujo `pregunta → /ask → respuesta + evidencia` funciona en navegador;
- nueva conversación reinicia `session_id`;
- errores HTTP se presentan al usuario;
- tests de rutas y assets pasan;
- API y Gauntlets anteriores no sufren regresiones.
