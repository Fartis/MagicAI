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
Open Judge Gauntlet                  ⏭️
JudgeResult estructurado             ⏳
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
- exclusión de cartas funny, silver-border, acorn y playtest.

Último checkpoint validado:

```text
3 seeds · 126/126 PASS · 14 concepts · 42 templates
```

---

## Sprint 10.14 — Open Judge Gauntlet ⏭️

Objetivo: medir lo que el Juez ya puede resolver fuera de rutas preparadas.

El conjunto incluirá preguntas heterogéneas sobre:

- lanzamiento y costes;
- objetivos y modos;
- combate;
- acciones basadas en estado;
- fichas;
- cambios de control;
- disparos y disparos retrasados;
- reemplazo y prevención;
- copias;
- Commander;
- cartas multiface;
- capas;
- preguntas ambiguas;
- premisas falsas.

Clasificación prevista:

```text
correct
correct_but_incomplete
needs_clarification
insufficient_evidence
false_premise
retrieval_failure
incorrect
hallucination
```

El resultado determinará la prioridad real de los siguientes sprints.

---

## Sprint 10.15 — Contrato `JudgeResult` ⏳

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

Objetivos:

- separar hechos, explicación y supuestos;
- permitir aclaraciones formales;
- exponer evidencia en la UI;
- ofrecer una API interna estable a otros perfiles;
- hacer los tests menos dependientes de coincidencias puramente léxicas.

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

## Fase 3 — UI modular del Juez ⏳

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
