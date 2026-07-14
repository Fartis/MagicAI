# 📊 Estado actual de MagicAI

> Snapshot de desarrollo: **v0.1.0-alpha**
> Última actualización documental: **14 de julio de 2026**

[Español](#-estado-del-proyecto) · [English](#-project-status)

---

## 🇪🇸 Estado del proyecto

MagicAI se encuentra en una **alpha funcional del Juez con UI beta local**. El pipeline principal recupera conocimiento local, resuelve referencias conversacionales, genera consultas de reglas, utiliza respuestas deterministas para familias cubiertas y valida la salida del LLM. El contrato `JudgeResult 1.0`, la salud de fuentes y la baseline abierta estable ya permiten utilizar el Juez desde la interfaz web.

No se considera un producto final porque aún faltan mayor cobertura guiada por fallos reales, pulido de experiencia, empaquetado, migraciones de datos y compatibilidad comprobada en más entornos.

### Capacidades implementadas

- Oracle y rulings locales de Scryfall.
- Comprehensive Rules locales con índice precalculado, postings y caché de consultas.
- Índice de cartas en memoria.
- Detección de cartas, aliases, keywords, acciones y reglas explícitas.
- Desambiguación conversacional de cartas con selección interactiva en la UI.
- Context Builder y Context Enricher.
- Recuperación de reglas guiada por pregunta y Oracle.
- Símbolos de Scryfall.
- Renderizadores deterministas de reglas y Oracle.
- Ollama local con temperatura cero.
- Validación de respuestas, reintento y fallback seguro.
- API REST con sesiones persistentes en SQLite y salida `JudgeResult` retrocompatible.
- UI beta local con chat, evidencia, estados, salud del servicio, copia y exportación.
- Informes TXT, XML y HTML.
- Replay de fallos dinámicos.
- Campañas multisemilla reanudables, paralelismo por procesos y cobertura acumulada.
- Open Judge Gauntlet con 11 conversaciones, 27 turnos y contratos semánticos.
- Community Feedback Gauntlet con entrada manual parafraseada, modo exploratorio `REVIEW_REQUIRED` y promoción posterior a contrato validado.
- Evaluation Campaign Runner reanudable, con checkpoints atómicos, reintento de errores y manifiesto reproducible.
- Exportación desde la UI de los turnos del usuario como caso exploratorio seguro, marcado como evaluación y sin respuestas objetivo.
- Clasificación separada de fallos de contexto, retrieval, contradicción y alucinación.
- `JudgeResult` con estado, origen, confianza, autoridad y evidencia de cartas y reglas.
- Trazabilidad del origen de respuesta, llamadas al LLM y tiempos por etapa en informes dinámicos.
- Escenarios de habilidades vinculados a una línea Oracle exacta y validados antes de ejecutar el Juez.

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

### Última campaña recibida y auditoría C1.4

La campaña C1.3 recibida desde el equipo de desarrollo ejecutó exactamente veinte semillas y cincuenta casos por semilla:

```text
Semillas                 20
Casos                  1.000
Conceptos cubiertos    14/14
Plantillas cubiertas   42/42
Cartas distintas          228
PASS del harness        1.000
WARN                        0
FAIL                        0
Llamadas al LLM             0
Origen determinista     1.000
Tiempo de pared          63,40 s
```

La huella de código y las fuentes declaradas por la campaña coinciden con el snapshot `source(27)`. El resultado confirma estabilidad y rendimiento, pero la auditoría humana y estructural encontró 23 escenarios de independencia de la fuente que necesitaban mayor precisión:

- seis habilidades con texto modal, instrucciones de activación o efectos mixtos mal clasificados;
- cuatro costes de sacrificio genéricos donde la fuente era una opción legal de pago;
- quince habilidades donde la fuente podía ser uno de los objetivos y la pregunta no lo excluía expresamente;
- dos escenarios pertenecían a más de una categoría.

Research C1.4 corrige esas familias de forma genérica:

- conserva los modos Oracle en varias líneas y sus viñetas;
- separa instrucciones de activación del efecto que realmente se resuelve;
- reconoce Monstrosity, Adapt, Level y efectos de prevención o redirección ligados a la fuente;
- distingue si la fuente debe salir como coste o solo podría elegirse para un coste genérico;
- distingue independencia de la fuente y legalidad de objetivos;
- añade a la pregunta premisas explícitas sobre qué objetos pagaron el coste y cuáles fueron los objetivos;
- exige que la respuesta explique por separado coste, fuente, última información conocida y objetivos ilegales;
- garantiza que `--oracle-file` use el mismo snapshot tanto para generar como para responder, también con procesos `spawn`.

### Validación previa a la campaña completa C1.4

```text
Matriz rápida y ampliada       231/231 PASS
Full-Oracle smoke                42/42 PASS
Replays exactos de hallazgos     23/23 PASS
Campaña reconstruida          1.000/1.000 PASS
Llamadas al LLM                       0
```

El smoke y los 23 replays utilizan el Oracle completo con el mismo SHA-256 de C1.3. La campaña de 1.000 utiliza un corpus mínimo reconstruido con las 228 cartas observadas en C1.3; valida las veinte semillas, los 42 contratos y cuatro procesos, pero no sustituye la repetición final contra el Oracle completo en el equipo del usuario.

### Open Judge Gauntlet

El Sprint 10.14 dispone de infraestructura y una baseline conversacional reproducible. La baseline completa validada tras 10.15b.1 alcanzó:

```text
Conversaciones ejecutadas       11
Turnos ejecutados               27
PASS                            21
STRATEGY_REQUIRED                4
NEEDS_CLARIFICATION              1
FALSE_PREMISE_HANDLED            1
Fallos críticos                  0
Errores de ejecución             0
```

El Sprint 10.15b amplía el corpus a 11 conversaciones y 27 turnos e incorpora:

- cantidades variables derivadas de Oracle, como `create X ... where X is ...`;
- separación explícita entre autoridad factual del Juez y recomendaciones de Deck Master;
- la categoría aceptable `STRATEGY_REQUIRED`;
- desambiguación abierta de Squee restringida a cartas jugables;
- actualización de la regla de exilio a 701.13 para evitar recuperar `Triple`;
- clasificación de cantidades numéricas incorrectas como contradicción factual.

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

- `JudgeResult` ya integra rulings locales bajo petición explícita, supuestos conservadores y corrección inicial de premisas falsas; falta ampliar estas familias según fallos reales.
- Las sesiones se persisten en SQLite local y se restauran tras reiniciar FastAPI. Todavía no hay sincronización entre equipos ni cifrado específico de la base local.
- La cobertura determinista todavía no abarca todas las familias de reglas.
- La cobertura de capas y dependencias ya tiene casos iniciales, pero todavía no es general; CDA, LKI, copias complejas, costes alternativos y cartas multiface necesitan más cobertura.
- El sistema no simula una partida completa como un motor de reglas digital.
- El soporte principal y mejor probado es el español; el inglés dispone de soporte parcial.
- La UI beta ya dispone de cancelación, timeout, desambiguación interactiva, copia/exportación, historial SQLite gestionable y presentación accesible. Falta seguir puliendo móvil, búsqueda de historial y ajustes de usuario.
- La baseline debe repetirse después de cambios que afecten al Juez o a sus contratos; los cambios puramente visuales se validan con tests de UI y smoke tests de API.
- Los casos comunitarios no se importan ni se consideran autoridad: entran manualmente, sin datos personales ni texto completo, y solo se versionan después de revalidarlos contra CR, Oracle y rulings actuales.
- Las campañas de feedback no entrenan el modelo, no modifican pesos y no promocionan resultados automáticamente; los fallos se convierten en cambios humanos de código y regresiones revisadas.

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

The Judge is not considered complete yet. The API now exposes a structured `JudgeResult` with local rulings, conservative assumptions and initial false-premise handling; the next milestones are stabilizing the contract and completing coverage driven by real failures.

The future UI will start with the Judge and later host Deck Master and Deckbuilder. Those profiles will use the Judge as their sole factual authority for card text, rules, rulings and legality.


### Preparación de API para UI beta — Sprint 10.15c

- `JudgeResult` versionado como schema `1.0`;
- `GET /meta` para descubrir versiones y enums;
- `GET /health` para fuentes locales y Ollama;
- errores HTTP estructurados y versionados;
- compatibilidad aditiva documentada;
- puerta de estabilidad para tres baselines Open Judge.

Puerta Open Judge completada: tres baselines consecutivas con 27/27 resultados aceptables, sin fallos críticos. Pendiente del Release Candidate formal: repetir la matriz controlada completa y los smoke tests finales del entorno objetivo.

## Sprint 11.0 — UI beta foundation ✅

Primera shell de usuario servida por FastAPI:

- ruta `/ui` y assets locales sin dependencias frontend adicionales;
- conversación con el Juez y continuidad mediante `session_id`;
- historial visual persistido localmente en el navegador;
- panel de cartas, reglas, rulings, supuestos y advertencias;
- estados, origen, confianza, schema y versiones de fuentes;
- indicador `/health`, errores estructurados y diseño responsive;
- construcción segura del DOM sin insertar respuestas mediante `innerHTML`.

La primera entrega no incluye cuentas, base de datos de conversaciones, acceso remoto endurecido ni Deck Master.


## Sprint 11.1 — usabilidad, resiliencia y presentación ✅

### 11.1a completado

- cancelación y timeout de consultas;
- protección frente a respuestas obsoletas;
- almacenamiento local validado y fallos visibles;
- allowlist de enlaces de Scryfall;
- anuncios accesibles y sondeo de salud no solapado.

### 11.1b implementado

- botones para resolver desambiguaciones sin escribir el nombre;
- copia de respuesta y evidencia;
- exportación del último `JudgeResult` en JSON;
- apertura automática y mejor jerarquía del panel de evidencia;
- `QUICKSTART.md` lineal y aclaración de ramas.

Pendiente para cerrar 11.1: revisión visual en navegador real, captura para README y correcciones de prioridad media-alta encontradas durante la aceptación manual.


## Sprint 11.2a — persistencia local e historial ✅

- conversaciones guardadas en SQLite local;
- contexto restaurable tras reiniciar FastAPI;
- endpoints de listado, detalle, renombrado y borrado;
- panel de historial en la UI;
- restauración del último `JudgeResult`;
- nuevo tema visual basado en la paleta del Gauntlet.

### Hotfix 11.2a.1 — copias de habilidades y fuente ausente

- recuperación prioritaria de las reglas 707.10, 113.7a, 608.2d, 405.5 y 117.3b;
- respuesta determinista para copias de habilidades cuya fuente abandona el campo;
- elecciones hechas al resolver tratadas de forma independiente para copia y original;
- validador que rechaza respuestas genéricas de prioridad que no contesten al escenario;
- regresión basada en una consulta real con Braids, Arisen Nightmare.

## Research C1.1 — campañas de evaluación reanudables ✅

- manifiesto `evaluation` con entrenamiento, aprendizaje y promoción automática desactivados;
- persistencia atómica por caso en `completed/` y `execution_errors/`;
- `--resume` sin repetición de casos completados;
- `--retry-errors` para repetir únicamente excepciones;
- huellas de casos y snapshots SHA-256 de fuentes locales;
- `findings_by_family.json`, `replay_commands.txt` y progreso recuperable;
- decisiones humanas de los paquetes de revisión preservadas entre checkpoints;
- UI consolidada con historial SQLite, cancelación y exportación segura al Gauntlet.
