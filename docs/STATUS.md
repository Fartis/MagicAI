# 📊 Estado actual de MagicAI

> Snapshot de desarrollo: **v0.1.0-alpha**
> Última actualización documental: **12 de julio de 2026**

[Español](#-estado-del-proyecto) · [English](#-project-status)

---

## 🇪🇸 Estado del proyecto

MagicAI se encuentra en una **alpha funcional del Juez**. El pipeline principal ya recupera conocimiento local, resuelve referencias conversacionales, genera consultas de reglas, utiliza respuestas deterministas para familias cubiertas y valida la salida del LLM.

No se considera finalizado porque todavía falta medir y ampliar su comportamiento ante preguntas abiertas, estabilizar una respuesta estructurada y cubrir familias de reglas complejas de alta frecuencia.

### Capacidades implementadas

- Oracle local de Scryfall.
- Comprehensive Rules locales y búsqueda por secciones.
- Índice de cartas en memoria.
- Detección de cartas, aliases, keywords, acciones y reglas explícitas.
- Desambiguación conversacional de cartas.
- Context Builder y Context Enricher.
- Recuperación de reglas guiada por pregunta y Oracle.
- Símbolos de Scryfall.
- Renderizadores deterministas de reglas y Oracle.
- Ollama local con temperatura cero.
- Validación de respuestas, reintento y fallback seguro.
- API REST con sesiones en memoria.
- Informes TXT, XML y HTML.
- Replay de fallos dinámicos.
- Campañas multisemilla y cobertura acumulada.
- Open Judge Gauntlet con 9 conversaciones, 25 turnos y contratos semánticos.
- Clasificación separada de fallos de contexto, retrieval, contradicción y alucinación.

### Conceptos dinámicos cubiertos

Los 14 conceptos actuales son:

```text
mana_ability
ward
source_independence
undying_exile
priority_during_resolution
stack_objects_one_by_one
cleanup_priority
commander_dies
commander_library_replacement
commander_copy
persist
persist_and_undying
counter_replacement_order
counters_as_enters
```

Cada concepto contiene tres plantillas controladas, para un total de **42 plantillas**.

### Última campaña validada

```text
Semillas                  3
Casos                   126
Conceptos cubiertos    14/14
Plantillas cubiertas   42/42
PASS                     126
WARN                       0
FAIL                       0
```

La campaña incluye escenarios `rules-only` y escenarios respaldados por cartas reales del Oracle local.

### Matriz de regresión validada

```text
Reddit Gauntlet          30/30
Generalization Probe     18/18
Dynamic Gauntlet         42/42
Dynamic Campaign        126/126
--------------------------------
Ejecuciones validadas   216/216
WARN                           0
FAIL                           0
```

### Open Judge Gauntlet

El Sprint 10.14 ya dispone de infraestructura y una primera baseline completa:

```text
Conversaciones ejecutadas        9
Turnos ejecutados               25
PASS                            10
CORRECT_BUT_INCOMPLETE           2
INSUFFICIENT_EVIDENCE            1
RETRIEVAL_FAILURE                3
CONTEXT_FAILURE                  9
Errores de ejecución             0
```

La auditoría manual detectó además falsos negativos del evaluador por variantes válidas como `Haste`/«prisa», «dibuja»/«roba» y «no se activa»/«no activa». El evaluador ya normaliza estas variantes y ahora detecta también afirmaciones demasiado absolutas, como fijar en seis el número de Kobolds de Prossh sin considerar el maná realmente gastado.

El hardening 10.14b añade continuidad conversacional genérica para:

- comparaciones que introducen una segunda carta;
- preguntas implícitas sobre la carta activa;
- keywords que comparten nombre con una carta;
- reglas numeradas referenciadas mediante pronombres;
- procedimientos sin carta, como London Mulligan;
- diferencias entre «al lanzar» y «al entrar»;
- costes de Oracle que exigen sacrificar «otra» criatura o permanente.

La Regression Suite y el Open Judge Gauntlet comparten el mismo corpus de preguntas. La primera sigue siendo útil para inspección humana; el segundo añade evaluación automática y estado conversacional.

Los últimos hardenings añadieron regresiones deterministas para:

- sacrificios pagados como coste y colocación posterior de disparos en la pila;
- referencias a la zona de mando aunque la pregunta no diga literalmente «comandante»;
- efectos continuos que comienzan en una capa y continúan en capas posteriores;
- dependencias entre efectos de cambio de tipo;
- separación de resultados cuando dos cartas similares producen interacciones distintas.

### Filtro de cartas del Gauntlet

El catálogo dinámico solo admite cartas:

- disponibles en papel;
- `legal` o `restricted` en al menos un formato soportado;
- no pertenecientes a productos `funny`;
- sin borde plateado;
- sin sello acorn;
- no marcadas como playtest.

Formatos considerados actualmente:

```text
standard
pioneer
modern
legacy
pauper
vintage
commander
standardbrawl
brawl
```

### Qué está validado con mayor confianza

- Ward como habilidad disparada.
- Habilidades de maná y uso de la pila.
- Independencia de una habilidad activada respecto a su fuente.
- Persist y Undying.
- Exilio frente a “morir”.
- Prioridad durante la resolución.
- Resolución de la pila objeto a objeto.
- Excepción de prioridad del paso de limpieza.
- Movimiento de comandantes entre zonas.
- Copias de comandantes.
- Orden de efectos de reemplazo sobre contadores.
- Contadores aplicados al entrar al campo de batalla.
- Sacrificio como coste frente a habilidades disparadas de muerte.
- Reconocimiento implícito del contexto Commander mediante la zona de mando.
- Cobertura inicial determinista de capas, continuidad y dependencias.

### Limitaciones conocidas

- La salida pública sigue siendo texto, no un objeto `JudgeResult` estructurado.
- Las sesiones de la API viven en memoria y no persisten tras reiniciar el proceso.
- La cobertura determinista todavía no abarca todas las familias de reglas.
- La cobertura de capas y dependencias ya tiene casos iniciales, pero todavía no es general; CDA, LKI, copias complejas, costes alternativos y cartas multiface necesitan más cobertura.
- El sistema no simula una partida completa como un motor de reglas digital.
- El soporte principal y mejor probado es el español; el inglés dispone de soporte parcial.
- La UI todavía no está implementada.
- La baseline debe repetirse después de cada hardening conversacional para medir la mejora real y detectar regresiones.

### Definición de “Juez finalizado y funcional”

El Juez v1 se considerará cerrado cuando:

1. Responda de forma fiable las familias de consultas prioritarias.
2. Devuelva evidencia estructurada de cartas, reglas y rulings.
3. Distinga entre respuesta, aclaración necesaria y evidencia insuficiente.
4. No invente Oracle, legalidad, reglas o premisas.
5. Mantenga campañas reproducibles sin regresiones inexplicadas.
6. Exponga una interfaz interna estable para UI, Deck Master y Deckbuilder.

---

## 🇬🇧 Project status

MagicAI is currently a **functional Judge alpha**. Its main pipeline retrieves local evidence, resolves conversational references, builds rule queries, uses deterministic answers for covered families and validates LLM output.

The latest validated dynamic campaign completed **126/126 cases**, covering **14 concepts** and **42 templates** across three seeds with no warnings or failures.

The Judge is not considered complete yet. The next milestones are an open-question evaluation suite, a structured `JudgeResult` contract, evidence-aware ambiguity handling and coverage driven by real failures.

The future UI will start with the Judge and later host Deck Master and Deckbuilder. Those profiles will use the Judge as their sole factual authority for card text, rules, rulings and legality.
