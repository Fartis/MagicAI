# 🏗️ Arquitectura de MagicAI

> Arquitectura actual del Juez y evolución prevista hacia una UI multiperfil.

[Español](#-arquitectura-actual) · [English](#-architecture-summary)

---

## 🇪🇸 Arquitectura actual

MagicAI separa recuperación, razonamiento, generación y validación. El LLM no consulta fuentes por su cuenta ni actúa como autoridad factual.

### Pipeline del Juez

```text
HTTP /ask or test harness
          │
          ▼
ConversationManager
          │
          ▼
MagicAI.ask / MagicAI.ask_result
          │
          ├── card disambiguation
          ├── conversation history
          └── active-card references
          │
          ▼
Context Builder
          │
          ├── deterministic intent hints
          ├── card extraction
          ├── keyword extraction
          ├── explicit rule extraction
          ├── action detection
          └── rule query generation
          │
          ▼
Context Enricher
          │
          ├── CardRepository → local Scryfall Oracle
          ├── RuleRepository → Comprehensive Rules
          ├── Oracle-derived rule queries
          └── Scryfall symbology
          │
          ▼
Knowledge Builder
          │
          ├── QUESTION
          ├── CARDS
          ├── SYMBOLS
          ├── RULES
          └── REASONING HINTS
          │
          ▼
Answer Generator
          │
          ├── deterministic Rule Renderer
          │        └── final answer when matched
          │
          └── Ollama when no deterministic answer exists
                   │
                   ▼
             answer validation
                   │
             ┌─────┴─────┐
             │           │
           valid       rejected
             │           │
             │         retry
             │           │
             │      safe fallback
             ▼           ▼
                 final answer
```

### Responsabilidades

#### `magicai.assistant`

Orquesta una consulta completa. No implementa reglas ni búsqueda directa.

#### `magicai.conversation`

Mantiene historial, cartas activas y estados pendientes de desambiguación. `ConversationManager` usa un repositorio SQLite local para restaurar las sesiones después de reiniciar FastAPI, conservando además una caché en memoria para la ejecución activa.

#### `magicai.context_builder`

Convierte la pregunta en un `AssistantContext`: intención, cartas, keywords, reglas explícitas, consultas semánticas y pistas de acciones.

#### `magicai.context_enricher`

Resuelve nombres de cartas, recupera reglas, añade símbolos y prioriza consultas derivadas del Oracle cuando la pregunta trata sobre habilidades.

#### `magicai.repositories` y `magicai.services`

Definen la frontera de acceso a cartas y reglas. El resto del pipeline no debería depender directamente del formato de los ficheros fuente.

#### `magicai.retrieval`

Genera consultas de reglas y conceptos Oracle. Aquí se resuelven muchos fallos de generalización lingüística.

#### `magicai.validation`

Contiene:

- renderizador determinista de reglas;
- renderizador Oracle;
- validadores de contradicciones y alucinaciones;
- fallback seguro basado en evidencia recuperada.

#### `magicai.llm`

Cliente de Ollama. El modelo recibe conocimiento preparado, no acceso directo a fuentes ni a Internet.

### Prioridad de evidencia

```text
Oracle recuperado
    > reglas recuperadas
        > rulings recuperados (futuro contrato formal)
            > pistas semánticas
                > memoria del modelo, que no es autoridad
```

Las pistas de razonamiento solo ayudan a interpretar la intención. Nunca sustituyen reglas.

---

## Renderizado determinista y LLM

MagicAI utiliza un enfoque híbrido:

1. Si la evidencia coincide con una familia formal cubierta, el `rule_renderer` genera una respuesta determinista.
2. Si no existe renderer, Ollama explica el contexto recuperado.
3. La respuesta del modelo se valida.
4. Si falla, se reintenta con las violaciones detectadas.
5. Si sigue fallando, se produce un fallback seguro.

Esto permite aprovechar la flexibilidad lingüística del LLM sin convertirlo en la fuente de verdad.

1. Si la evidencia coincide con una familia formal cubierta, el `rule_renderer` genera una respuesta determinista.
2. Si no existe renderer, Ollama explica el contexto recuperado.
3. La respuesta del modelo se valida.
4. Si falla, se reintenta con las violaciones detectadas.
5. Si sigue fallando, se produce un fallback seguro.

## Arquitectura de pruebas

```text
Unit and contract tests
├── retrieval
├── card extraction
├── renderers
├── validation
└── campaign planning

Fixed quality suites
├── Reddit Gauntlet
├── Generalization Probe
└── Regression Suite

Generated quality suites
├── Dynamic Gauntlet
│   ├── card-backed scenarios
│   └── rules-only scenarios
└── Multiseed Campaign
    ├── per-seed manifest
    ├── replayable failures
    └── aggregate coverage
```

El Gauntlet no solo evalúa la respuesta. También conserva la carta elegida, Oracle, tipo, set, legalidad, plantilla y contrato para auditar premisas falsas.

---

## Arquitectura futura multiperfil

La UI será una única aplicación modular. El Juez será el primer perfil disponible.

```text
MagicAI UI
    │
    ▼
Profile Router
    │
    ├── Judge
    │     └── factual authority
    │
    ├── Deck Master
    │     ├── deck evaluation
    │     ├── game plans
    │     ├── mulligans
    │     └── matchup strategy
    │
    └── Deckbuilder
          ├── build from zero
          ├── improve a list
          ├── packages and curve
          └── budget and power targets
```

### Jerarquía de autoridad futura

```text
Evidencia
   │
   ▼
Juez
   │  hechos, reglas, Oracle, legalidad e interacciones validadas
   ▼
Deck Master
   │  criterio estratégico validado sobre jugadas y planes de mazo
   ▼
Deckbuilder
      propuestas concretas de construcción y modificación
```

- **Juez:** autoridad factual y reglamentaria absoluta.
- **Deck Master:** autoridad estratégica, siempre subordinada a los hechos del Juez.
- **Deckbuilder:** motor de propuestas; necesita validación factual del Juez y validación estratégica de Deck Master.

Deck Master y Deckbuilder:

- no consultarán Scryfall directamente;
- no consultarán Comprehensive Rules directamente;
- no usarán Internet para afirmar texto, legalidad o reglas;
- no inventarán interacciones;
- recibirán evidencia factual únicamente mediante el Juez.

Una propuesta del Deckbuilder solo se presentará como validada cuando tenga las dos firmas:

```text
FACTUAL_VALIDATION   = Judge
STRATEGIC_VALIDATION = Deck Master
```

La sesión futura será compartida entre perfiles y conservará un `authority_trace` para distinguir hechos, recomendaciones y propuestas.

Deck Master y Deckbuilder:

## Contrato `JudgeResult`

La API conserva `answer` y `session_id`, pero ya expone una primera versión estructurada del resultado factual del Juez:

```json
{
  "status": "answered",
  "origin": "deterministic_rule",
  "confidence": "high",
  "authority": "judge",
  "answer": "...",
  "cards": [],
  "rules": [],
  "rulings": [],
  "retrieval_queries": [],
  "assumptions": [],
  "warnings": [],
  "source_versions": {},
  "validation_attempts": 0
}
```

Estados previstos:

```text
answered
needs_clarification
insufficient_evidence
strategy_required
false_premise
```

`origin` distingue desambiguación, renderizadores deterministas, LLM validado, frontera estratégica y fallback seguro. El contrato será utilizado por:

- la UI;
- Deck Master;
- Deckbuilder;
- tests de integración;
- exportación y auditoría.

---

## Decisiones de diseño no negociables

- El Juez es la autoridad factual única.
- Los fixes deben ser genéricos, no hardcodes de cartas o preguntas.
- Una premisa falsa invalida un PASS aunque la explicación abstracta sea correcta.
- Las cartas de broma, silver-border, acorn y playtest quedan fuera del flujo estándar.
- La incertidumbre debe expresarse, no rellenarse con memoria del modelo.
- La UI no contendrá conocimiento de Magic; solo presentará perfiles, respuestas y evidencia.

---

## 🇬🇧 Architecture summary

MagicAI separates retrieval, generation and validation. The Judge builds a grounded context from local Oracle data, Comprehensive Rules and conversation state. Deterministic renderers answer covered rule families; Ollama handles the remaining explanations under strict validation and safe fallback rules.

The future UI will host multiple profiles. Deck Master and Deckbuilder will remain strategically creative but will have no direct factual access to card or rules sources. They must request Oracle text, legality, rulings and interaction validation through the Judge.
