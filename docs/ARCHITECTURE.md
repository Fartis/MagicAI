# 🏗 Architecture

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Arquitectura

MagicAI está diseñado siguiendo una filosofía muy simple:

> **Cada componente debe tener una única responsabilidad.**

En lugar de construir un asistente monolítico donde toda la lógica se mezcla, MagicAI divide el proceso de razonamiento en pequeños bloques independientes.

Esto facilita:

- 🧩 Mantener el código
- ⚡ Optimizar componentes individuales
- 🧪 Probar cada etapa por separado
- 🔄 Sustituir implementaciones sin afectar al resto del sistema

Cada respuesta es el resultado de un pipeline donde cada componente aporta únicamente el conocimiento necesario para la siguiente etapa.

</td>

<td width="50%" valign="top">

# 🇬🇧 Architecture

MagicAI follows one simple principle:

> **Each component should have a single responsibility.**

Instead of building one monolithic assistant where every task happens at once, MagicAI divides the reasoning process into small independent stages.

This makes it easier to:

- 🧩 Maintain the codebase
- ⚡ Optimize individual components
- 🧪 Test each stage independently
- 🔄 Replace implementations without affecting the rest of the system

Every answer is produced by a pipeline where each component contributes only the knowledge required for the next stage.

</td>

</tr>
</table>

---

# 📊 High-Level Architecture

```
                         User
                           │
                           ▼
                    MagicAI Assistant
                           │
                           ▼
                     Conversation
                           │
                           ▼
                    Context Builder
                           │
                           ▼
                   Context Enricher
                           │
                           ▼
                  Knowledge Builder
                           │
                           ▼
                      Ollama (LLM)
                           │
                           ▼
                        Response
```

---

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Flujo de una consulta

Cada pregunta sigue exactamente el mismo recorrido.

1. El usuario realiza una pregunta.
2. Se recupera el historial de conversación.
3. Se identifican cartas, reglas y referencias implícitas.
4. Se construye un contexto estructurado.
5. El conocimiento se entrega al LLM.
6. El modelo genera una respuesta utilizando únicamente dicho contexto.

El modelo nunca recibe únicamente la pregunta del usuario.

Siempre recibe conocimiento previamente preparado.

</td>

<td width="50%" valign="top">

# 🇬🇧 Request Flow

Every question follows the same execution pipeline.

1. The user asks a question.
2. Conversation history is retrieved.
3. Cards, rules and implicit references are extracted.
4. A structured context is built.
5. Knowledge is sent to the language model.
6. The LLM generates an answer using that knowledge.

The language model never receives only the user's question.

It always receives structured knowledge first.

</td>

</tr>
</table>

---

# 🧩 Components

<table>
<tr>

<td width="50%" valign="top">

## 🧠 Assistant

Punto de entrada principal del sistema.

Coordina el pipeline completo y mide el rendimiento de cada etapa.

---

## 💬 Conversation

Mantiene el estado de la conversación.

Permite resolver preguntas como:

> "¿Y si lo sacrifico?"

sin repetir el nombre de la carta.

---

## 🔍 Context Builder

Detecta automáticamente:

- cartas
- palabras clave
- reglas relevantes
- referencias implícitas

Su objetivo es comprender **de qué está hablando el usuario**.

---

## 📚 Context Enricher

Amplía el contexto recuperando información adicional cuando es necesario.

Añade únicamente conocimiento útil.

Nunca inventa información.

---

## 🧠 Knowledge Builder

Organiza toda la información recopilada en un formato estructurado que el LLM pueda interpretar fácilmente.

Es el último paso antes de la inferencia.

---

## 🤖 Ollama

El modelo de lenguaje.

Su única responsabilidad es transformar el conocimiento proporcionado en una explicación comprensible.

No es la fuente de verdad.

Es el narrador.

</td>

<td width="50%" valign="top">

## 🧠 Assistant

Main entry point.

Coordinates the complete pipeline and measures the execution time of every stage.

---

## 💬 Conversation

Stores the conversation state.

Allows follow-up questions like:

> "What if I sacrifice it?"

without mentioning the card again.

---

## 🔍 Context Builder

Automatically detects:

- cards
- keywords
- relevant rules
- implicit references

Its goal is understanding **what the player is talking about**.

---

## 📚 Context Enricher

Expands the retrieved context whenever additional knowledge is required.

Only useful information is added.

Nothing is invented.

---

## 🧠 Knowledge Builder

Organizes all collected information into a structured format for the language model.

This is the final stage before inference.

---

## 🤖 Ollama

The language model.

Its only responsibility is transforming structured knowledge into a clear explanation.

It is not the source of truth.

It is the storyteller.

</td>

</tr>
</table>

---

# 🎯 Design Principles

<table>
<tr>

<td width="50%" valign="top">

MagicAI sigue cinco principios fundamentales.

## 📖 Official Knowledge First

La información oficial siempre tiene prioridad sobre el conocimiento del modelo.

---

## 🧩 Single Responsibility

Cada componente hace una sola cosa.

Y procura hacerla bien.

---

## 🧠 Context Engineering

Es mejor mejorar el contexto que hacer prompts cada vez más largos.

---

## 🔄 Modular Design

Cada componente puede sustituirse sin modificar el resto del sistema.

---

## 🧪 Test Everything

Toda mejora importante debe poder verificarse mediante pruebas automáticas.

</td>

<td width="50%" valign="top">

MagicAI follows five core principles.

## 📖 Official Knowledge First

Official sources always take precedence over the model's memory.

---

## 🧩 Single Responsibility

Each component performs exactly one task.

And aims to do it well.

---

## 🧠 Context Engineering

Improving the context is better than endlessly expanding prompts.

---

## 🔄 Modular Design

Every component can be replaced independently.

---

## 🧪 Test Everything

Every important improvement should be validated through automated tests.

</td>

</tr>
</table>

---

# 🔮 Future Evolution

<table>
<tr>

<td width="50%" valign="top">

La arquitectura está preparada para crecer.

Las próximas versiones podrán incorporar nuevos componentes como:

- ⚡ Caché
- 🎴 Índice de cartas
- 🧠 Grafo de conocimiento
- 📊 Métricas
- 🌐 Frontend
- 🐳 Docker

sin modificar el flujo principal.

La arquitectura fue diseñada para evolucionar sin romper compatibilidad.

</td>

<td width="50%" valign="top">

The architecture is designed to evolve.

Future versions may introduce new components such as:

- ⚡ Cache
- 🎴 Card Index
- 🧠 Knowledge Graph
- 📊 Metrics
- 🌐 Frontend
- 🐳 Docker

without changing the core pipeline.

The architecture is built to grow without breaking compatibility.

</td>

</tr>
</table>

---

<div align="center">

### 🧙

**Good software answers questions.**

**Great software explains how it reached the answer.**

</div>