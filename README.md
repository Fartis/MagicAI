<div align="center">

# 🧙 MagicAI

## *More Gathering. Less Guessing.*

### *The IABuilding Project*

*"Asking a generic LLM how a Magic interaction works is fine...*

*...but building one that consults the official rules, remembers the conversation and runs entirely locally is far more fun."*

---

### 🇪🇸 Una IA especializada en *Magic: The Gathering*, ejecutándose completamente en local.

### 🇬🇧 An AI specialized in *Magic: The Gathering*, running entirely locally.

</div>

---

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Español

## ¿Qué es MagicAI?

MagicAI es un asistente conversacional especializado en **Magic: The Gathering** cuyo objetivo es responder preguntas utilizando exclusivamente información oficial del juego.

En lugar de depender únicamente del conocimiento almacenado en un modelo de lenguaje, MagicAI construye dinámicamente el contexto de cada conversación utilizando diferentes fuentes de conocimiento.

### 📖 Fuentes utilizadas

- Oracle oficial de Scryfall
- Magic Comprehensive Rules
- Contexto de la conversación
- Recuperación inteligente de cartas y reglas

Todo ello ejecutándose **100% en local** mediante **Ollama**, sin depender de APIs externas.

MagicAI **no intenta memorizar Magic**.

Prefiere **consultar**, **razonar** y **explicar** utilizando las fuentes oficiales.

---

## 💡 Filosofía

Los modelos de lenguaje son increíblemente buenos explicando conceptos.

Sin embargo, cuando se trata de un juego tan complejo como Magic, la respuesta correcta depende del contexto, de las reglas oficiales y de miles de interacciones posibles.

MagicAI nace con una idea muy sencilla:

> **Menos alucinaciones. Más conocimiento.**

En lugar de pedirle al modelo que "recuerde" cómo funciona Magic, se le proporciona toda la información necesaria para que pueda responder correctamente.

La IA no sustituye las reglas.

Las interpreta.

</td>

<td width="50%" valign="top">

# 🇬🇧 English

## What is MagicAI?

MagicAI is a conversational assistant specialized in **Magic: The Gathering**, designed to answer questions using only the game's official sources.

Instead of relying exclusively on what a language model remembers, MagicAI dynamically builds the context of every conversation using multiple knowledge sources.

### 📖 Knowledge Sources

- Official Scryfall Oracle
- Magic Comprehensive Rules
- Conversation context
- Intelligent card and rule retrieval

Everything runs **100% locally** through **Ollama**, without relying on external AI APIs.

MagicAI **doesn't try to memorize Magic**.

Instead, it prefers to **retrieve**, **reason** and **explain** using official information.

---

## 💡 Philosophy

Language models are incredibly good at explaining concepts.

However, Magic is an extremely complex game where the correct answer often depends on context, official rules and thousands of possible interactions.

MagicAI is built around one simple idea:

> **Less hallucination. More knowledge.**

Rather than asking an LLM to "remember" how Magic works, MagicAI provides the model with the official information it needs to generate accurate explanations.

The AI doesn't replace the rules.

It interprets them.

</td>

</tr>
</table>

---

## ✨ Core Principles

- 🎴 Official Oracle before memory.
- 📚 Official Rules before assumptions.
- 💬 Conversation before isolated prompts.
- 🧠 Context before completion.
- ⚡ Local-first AI.
- ❤️ Built by a Magic player, for Magic players.

---
# ✨ Features

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Características

MagicAI ha sido diseñado siguiendo una arquitectura modular donde cada componente tiene una única responsabilidad.

### 🎴 Reconocimiento inteligente de cartas

- Detección automática de nombres de cartas.
- Resolución de referencias implícitas.
- Recuperación de cartas mencionadas anteriormente.
- Soporte para conversaciones naturales.

---

### 📚 Motor de reglas

MagicAI consulta automáticamente las **Magic Comprehensive Rules** cuando detecta preguntas relacionadas con:

- Habilidades
- Mecánicas
- Palabras clave
- Prioridad
- Pila
- Efectos continuos
- Capas
- Estado del juego

---

### 💬 Memoria conversacional

Cada conversación mantiene su propio contexto.

Esto permite realizar preguntas como:

> "¿Y si lo sacrifico?"

sin necesidad de volver a mencionar la carta.

---

### 🧠 Construcción dinámica del contexto

MagicAI construye automáticamente el conocimiento que necesita el modelo antes de cada consulta.

Combina:

- Oracle
- Reglas
- Conversación
- Cartas relacionadas

para generar un único contexto consistente.

---

### ⚡ Local First

Toda la inferencia se realiza en local mediante **Ollama**.

No se envían cartas, conversaciones ni preguntas a servicios externos.

---

### 🧪 Desarrollo orientado a pruebas

El proyecto incorpora:

- Regression Suite
- Performance Suite

para detectar regresiones funcionales y medir el rendimiento tras cada cambio.

</td>

<td width="50%" valign="top">

# 🇬🇧 Features

MagicAI follows a modular architecture where every component has a single responsibility.

### 🎴 Intelligent Card Recognition

- Automatic card name detection.
- Implicit reference resolution.
- Previous card retrieval.
- Natural conversation support.

---

### 📚 Rules Engine

MagicAI automatically consults the **Magic Comprehensive Rules** whenever a question involves:

- Abilities
- Mechanics
- Keywords
- Priority
- The Stack
- Continuous effects
- Layers
- Game state

---

### 💬 Conversation Memory

Each conversation keeps its own context.

This allows natural follow-up questions such as:

> "What if I sacrifice it?"

without mentioning the card again.

---

### 🧠 Dynamic Context Building

Before every question, MagicAI automatically prepares the information required by the language model.

It combines:

- Oracle
- Rules
- Conversation
- Related cards

into a single coherent context.

---

### ⚡ Local First

Every inference runs locally through **Ollama**.

No cards, conversations or questions leave your computer.

---

### 🧪 Test Driven Development

MagicAI includes:

- Regression Suite
- Performance Suite

to detect regressions and monitor performance after every change.

</td>

</tr>
</table>

---

# 🏗 Architecture

<table>
<tr>

<td width="50%" valign="top">

## 🇪🇸 Flujo de trabajo

Cada pregunta sigue exactamente el mismo recorrido.

```text
Usuario

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

Ollama

    │

    ▼

Respuesta
```

Cada módulo tiene una única responsabilidad.

Esto hace que el proyecto sea sencillo de mantener y ampliar.

---

### Componentes principales

| Componente | Función |
|------------|----------|
| Conversation | Memoria de la conversación |
| Context Builder | Construcción del contexto inicial |
| Context Enricher | Recuperación de cartas y reglas |
| Knowledge Builder | Preparación del prompt |
| Ollama | Inferencia del LLM |

</td>

<td width="50%" valign="top">

## 🇬🇧 Workflow

Every question follows the exact same pipeline.

```text
User

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

Ollama

   │

   ▼

Answer
```

Each module has a single responsibility.

Keeping components isolated makes the project easier to maintain and extend.

---

### Main Components

| Component | Responsibility |
|-----------|----------------|
| Conversation | Conversation memory |
| Context Builder | Initial context creation |
| Context Enricher | Card & rule retrieval |
| Knowledge Builder | Prompt preparation |
| Ollama | LLM inference |

</td>

</tr>
</table>

---
# 🚀 Quick Start

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Primeros pasos

## Requisitos

MagicAI ha sido desarrollado y probado con:

- 🐍 Python **3.12+**
- 🤖 Ollama
- 🧠 Un modelo compatible (recomendado **Qwen3:8B**)
- 💻 Linux / Windows (WSL2) / macOS

---

## Instalación

```bash
git clone https://github.com/<usuario>/MagicAI.git

cd MagicAI

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

pip install -e .
```

---

## Descargar las fuentes oficiales

```bash
./scripts/download_sources.sh

./scripts/download_rules.sh
```

---

## Iniciar la API REST

```bash
uvicorn magicai.api:app --reload
```

---

## Swagger

Una vez iniciada la API:

```
http://localhost:8000/docs
```

---

## ReDoc

```
http://localhost:8000/redoc
```

---

## Ejecutar los tests

Performance

```bash
python tests/test_performance.py
```

Regression Suite

```bash
python tests/regression/regression_test.py
```

</td>

<td width="50%" valign="top">

# 🇬🇧 Getting Started

## Requirements

MagicAI has been developed and tested with:

- 🐍 Python **3.12+**
- 🤖 Ollama
- 🧠 A compatible model (recommended **Qwen3:8B**)
- 💻 Linux / Windows (WSL2) / macOS

---

## Installation

```bash
git clone https://github.com/<user>/MagicAI.git

cd MagicAI

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

pip install -e .
```

---

## Download official sources

```bash
./scripts/download_sources.sh

./scripts/download_rules.sh
```

---

## Start REST API

```bash
uvicorn magicai.api:app --reload
```

---

## Swagger UI

After starting the API:

```
http://localhost:8000/docs
```

---

## ReDoc

```
http://localhost:8000/redoc
```

---

## Run tests

Performance

```bash
python tests/test_performance.py
```

Regression Suite

```bash
python tests/regression/regression_test.py
```

</td>

</tr>
</table>

---

# 📁 Project Structure

<table>
<tr>

<td width="50%" valign="top">

## 🇪🇸 Organización

```
MagicAI/

├── magicai/
│   ├── api/
│   ├── assistant/
│   ├── conversation/
│   ├── extractors/
│   ├── llm/
│   ├── repositories/
│   ├── services/
│   ├── prompts/
│   ├── nlp/
│   └── ...
│
├── prompts/
│
├── scripts/
│
├── sources/
│
├── tests/
│   ├── regression/
│   └── test_performance.py
│
├── models/
│
└── README.md
```

---

### Directorios principales

| Carpeta | Descripción |
|----------|-------------|
| `assistant/` | Núcleo de MagicAI |
| `conversation/` | Gestión del contexto |
| `extractors/` | Extracción de cartas |
| `repositories/` | Acceso a datos |
| `services/` | Lógica de negocio |
| `llm/` | Integración con Ollama |
| `tests/` | Testing automatizado |

</td>

<td width="50%" valign="top">

## 🇬🇧 Structure

```
MagicAI/

├── magicai/
│   ├── api/
│   ├── assistant/
│   ├── conversation/
│   ├── extractors/
│   ├── llm/
│   ├── repositories/
│   ├── services/
│   ├── prompts/
│   ├── nlp/
│   └── ...
│
├── prompts/
│
├── scripts/
│
├── sources/
│
├── tests/
│   ├── regression/
│   └── test_performance.py
│
├── models/
│
└── README.md
```

---

### Main Directories

| Folder | Description |
|----------|-------------|
| `assistant/` | MagicAI core |
| `conversation/` | Conversation memory |
| `extractors/` | Card extraction |
| `repositories/` | Data access |
| `services/` | Business logic |
| `llm/` | Ollama integration |
| `tests/` | Automated testing |

</td>

</tr>
</table>

---
# 🧪 Testing & Benchmark

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Testing

MagicAI ha sido desarrollado con una filosofía muy sencilla:

> **Cada nueva funcionalidad debe poder demostrarse que funciona.**

Para ello el proyecto incorpora varias suites de pruebas.

---

## 🔄 Regression Suite

La Regression Suite reproduce conversaciones reales para comprobar que nuevas modificaciones no rompen funcionalidades existentes.

Actualmente se validan aspectos como:

- 🎴 Reconocimiento automático de cartas.
- 💬 Persistencia del contexto conversacional.
- 📚 Recuperación de reglas oficiales.
- 🔎 Resolución de referencias implícitas.
- ⚔️ Comparación entre cartas.
- 🧠 Recuperación de contexto.
- 🃏 Interacciones complejas.
- 📖 Consultas sobre habilidades.

### Ejemplo

```
¿Qué hace Young Wolf?

↓

¿Y si muere?

↓

¿Y si lo sacrifico?

↓

¿Y si lo exilio?
```

Todo ello sin volver a mencionar la carta.

---

## ⚡ Performance Suite

Además de comprobar que la IA responde correctamente, también se mide el rendimiento de cada consulta.

Actualmente se monitoriza:

- Context Builder
- Context Enricher
- Knowledge Builder
- Tiempo de inferencia del LLM
- Tiempo total de respuesta

Ejemplo:

```
Context Builder : 0.82s
Context Enricher: 0.01s
Knowledge       : 0.00s
LLM             : 5.28s
TOTAL           : 6.11s
```

---

## 🎯 Objetivo

No se busca únicamente que MagicAI responda correctamente.

También se busca que siga haciéndolo después de cientos de modificaciones.

Cada nueva versión debe ser:

- Más rápida.
- Más estable.
- Más inteligente.

</td>

<td width="50%" valign="top">

# 🇬🇧 Testing

MagicAI follows one very simple philosophy:

> **Every new feature should be verifiable.**

For that reason the project includes multiple automated test suites.

---

## 🔄 Regression Suite

The Regression Suite reproduces real conversations to ensure new changes never break existing behaviour.

Current scenarios include:

- 🎴 Automatic card recognition.
- 💬 Conversation memory.
- 📚 Official rules retrieval.
- 🔎 Implicit reference resolution.
- ⚔️ Card comparisons.
- 🧠 Context recovery.
- 🃏 Complex interactions.
- 📖 Keyword explanations.

### Example

```
What does Young Wolf do?

↓

What if it dies?

↓

What if I sacrifice it?

↓

What if I exile it?
```

All without mentioning the card again.

---

## ⚡ Performance Suite

Besides correctness, MagicAI continuously measures performance.

Current metrics include:

- Context Builder
- Context Enricher
- Knowledge Builder
- LLM inference
- Total response time

Example:

```
Context Builder : 0.82s
Context Enricher: 0.01s
Knowledge       : 0.00s
LLM             : 5.28s
TOTAL           : 6.11s
```

---

## 🎯 Goal

MagicAI isn't only expected to answer correctly.

It is expected to keep answering correctly after hundreds of future improvements.

Every release should become:

- Faster.
- More stable.
- Smarter.

</td>

</tr>
</table>

---

# 📊 Project Status

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Estado actual

**Versión**

```text
v0.1.0-alpha
```

---

## ✅ Implementado

- ✔️ Arquitectura modular.
- ✔️ Integración con Ollama.
- ✔️ Conversaciones persistentes.
- ✔️ Recuperación automática de cartas.
- ✔️ Recuperación de reglas.
- ✔️ API REST.
- ✔️ Regression Suite.
- ✔️ Performance Suite.
- ✔️ Compatible con CPU.
- ✔️ Compatible con GPU (CUDA).

---

## 📈 Resultados actuales

- 🧪 Regression Suite

```
25 preguntas

0 errores
```

- ⚡ Tiempo medio de respuesta

```
≈ 6 segundos

RTX 4060 Ti
```

---

## 🟢 Estado

MagicAI se encuentra actualmente en una fase **Alpha funcional**.

La arquitectura principal está consolidada y el desarrollo se centra ahora en mejorar el rendimiento y ampliar funcionalidades.

</td>

<td width="50%" valign="top">

# 🇬🇧 Current Status

**Version**

```text
v0.1.0-alpha
```

---

## ✅ Implemented

- ✔️ Modular architecture.
- ✔️ Ollama integration.
- ✔️ Persistent conversations.
- ✔️ Automatic card retrieval.
- ✔️ Rules retrieval.
- ✔️ REST API.
- ✔️ Regression Suite.
- ✔️ Performance Suite.
- ✔️ CPU support.
- ✔️ GPU acceleration (CUDA).

---

## 📈 Current Results

- 🧪 Regression Suite

```
25 questions

0 errors
```

- ⚡ Average response time

```
≈ 6 seconds

RTX 4060 Ti
```

---

## 🟢 Status

MagicAI is currently in a **functional Alpha** stage.

Its core architecture is stable, and future development focuses on performance improvements and new capabilities.

</td>

</tr>
</table>

---
# 🗺️ Roadmap

<table>
<tr>

<td width="50%" valign="top">

# 🇪🇸 Próximos pasos

MagicAI ha alcanzado un punto donde la arquitectura principal es estable.

Las próximas versiones estarán orientadas a mejorar la experiencia de uso, el rendimiento y las capacidades del asistente.

---

## 🚀 Rendimiento

- [ ] Card Index para acelerar la detección de cartas.
- [ ] Sistema de caché para consultas repetidas.
- [ ] Optimización del Context Builder.
- [ ] Optimización del Context Enricher.
- [ ] Benchmark avanzado.
- [ ] Métricas de Ollama (tokens/s, VRAM, timings...).

---

## 🧠 Inteligencia

- [ ] Resolución de ambigüedades (*Persist* carta vs habilidad).
- [ ] Comparaciones automáticas entre cartas.
- [ ] Mejor recuperación del contexto.
- [ ] Detección inteligente de referencias implícitas.
- [ ] Explicaciones paso a paso de reglas complejas.

---

## 🌐 Plataforma

- [ ] Frontend estilo ChatGPT.
- [ ] Streaming de respuestas.
- [ ] Gestión de múltiples conversaciones.
- [ ] Configuración desde interfaz web.
- [ ] Selección dinámica de modelos LLM.

---

## 🎴 Magic

- [ ] Soporte para Commander.
- [ ] Consultas sobre deckbuilding.
- [ ] Sugerencias de cartas.
- [ ] Análisis de sinergias.
- [ ] Explicación de combos.
- [ ] Importación de mazos (Moxfield, Archidekt...).

---

## ❤️ Comunidad

- [ ] Documentación completa.
- [ ] Wiki del proyecto.
- [ ] Ejemplos de integración.
- [ ] Guía para colaboradores.
- [ ] Publicación oficial en GitHub.

</td>

<td width="50%" valign="top">

# 🇬🇧 Roadmap

MagicAI has reached a point where its core architecture is stable.

Future releases will focus on usability, performance and new capabilities.

---

## 🚀 Performance

- [ ] Card Index for faster card detection.
- [ ] Query cache.
- [ ] Context Builder optimization.
- [ ] Context Enricher optimization.
- [ ] Advanced benchmark.
- [ ] Ollama metrics (tokens/s, VRAM, timings...).

---

## 🧠 Intelligence

- [ ] Ambiguity resolution (*Persist* card vs keyword).
- [ ] Automatic card comparisons.
- [ ] Improved context retrieval.
- [ ] Better implicit reference detection.
- [ ] Step-by-step rules explanations.

---

## 🌐 Platform

- [ ] ChatGPT-like frontend.
- [ ] Response streaming.
- [ ] Multi-conversation support.
- [ ] Web configuration.
- [ ] Dynamic LLM selection.

---

## 🎴 Magic

- [ ] Commander support.
- [ ] Deckbuilding assistant.
- [ ] Card suggestions.
- [ ] Synergy analysis.
- [ ] Combo explanations.
- [ ] Deck import (Moxfield, Archidekt...).

---

## ❤️ Community

- [ ] Complete documentation.
- [ ] Project wiki.
- [ ] Integration examples.
- [ ] Contributor guide.
- [ ] Public GitHub release.

</td>

</tr>
</table>

---

# 🃏 IABuilding

<table>
<tr>

<td width="50%" valign="top">

## 🇪🇸

*"Deckbuilding siempre ha sido una de mis partes favoritas de Magic.*

*Construir una IA terminó siendo sorprendentemente parecido."*

Todo empieza con una idea.

Después llegan las pruebas.

Los errores.

Los cambios.

Las mejoras.

Las partidas.

Y vuelta a empezar.

Porque construir una buena IA se parece mucho a construir un buen mazo.

Nunca está realmente terminada.

Siempre hay una interacción nueva por descubrir.

Siempre hay una mejor decisión que tomar.

Siempre hay una carta que probar.

MagicAI nace con esa misma filosofía.

No busca sustituir al jugador.

Busca ayudarle a entender mejor el juego.

Y, sobre todo...

a disfrutar descubriendo todas las posibilidades que ofrece.

</td>

<td width="50%" valign="top">

## 🇬🇧

*"Deckbuilding has always been one of my favourite parts of Magic.*

*Building an AI turned out to be surprisingly similar."*

Everything starts with an idea.

Then comes testing.

Mistakes.

Improvements.

Games.

Iteration.

Because building a great AI feels a lot like building a great deck.

It is never truly finished.

There is always another interaction to discover.

Always a better decision to make.

Always another card worth trying.

MagicAI follows that same philosophy.

It doesn't aim to replace the player.

It aims to help them understand the game.

And, above all...

to enjoy discovering everything Magic has to offer.

</td>

</tr>
</table>

---

# ❤️ Thank You · Gracias

<table>
<tr>

<td width="50%" valign="top">

## 🇪🇸

Si has llegado hasta aquí...

Gracias.

Ya sea corrigiendo una errata, proponiendo una mejora, reportando un bug o simplemente compartiendo una idea...

Estás ayudando a construir MagicAI.

Los mejores mazos rara vez los construye una sola persona.

Creo que los mejores proyectos Open Source tampoco.

**Bienvenido al Gathering.**

</td>

<td width="50%" valign="top">

## 🇬🇧

If you've made it this far...

Thank you.

Whether you're fixing a typo, reporting a bug, proposing an improvement or simply sharing an idea...

You're helping build MagicAI.

The best decks are rarely built by one person alone.

I believe the same is true for Open Source.

**Welcome to the Gathering.**

</td>

</tr>
</table>

---

<div align="center">

## ✨

> **Magic isn't just played.**
>
> **It's understood.**

MagicAI exists to help players discover the magic hidden between the rules.

---
---

# ❤️ Una carta personal

<table>
<tr>

<td width="50%" valign="top">

## 🇪🇸

Si has llegado hasta aquí, probablemente compartamos una misma afición.

Quería terminar este README con unas palabras más personales.

Por motivos de salud, es muy posible que este sea el último gran proyecto de programación que pueda desarrollar. Después de dedicar gran parte de mi vida profesional al desarrollo de software, ha llegado el momento de aceptar que mi camino tendrá que tomar otra dirección, mucho antes de lo que jamás imaginé.

Quería despedirme de esta etapa haciendo algo que uniera mis dos grandes pasiones: la programación y **Magic: The Gathering**, un juego que me ha acompañado durante prácticamente toda mi vida y que, en muchos momentos, ha sido mucho más que un simple juego.

MagicAI nació con una idea muy sencilla: construir la herramienta que a mí mismo me hubiera gustado tener para comprender mejor las reglas, organizar ideas y seguir disfrutando de este maravilloso juego.

Mientras mi salud me lo permita, seguiré mejorándolo poco a poco, aprendiendo y añadiendo nuevas funcionalidades.

Si este proyecto consigue ayudar aunque solo sea a un jugador a resolver una duda, descubrir una interacción nueva o simplemente disfrutar un poco más de Magic, habrá cumplido con creces su propósito.

Gracias por dedicar parte de tu tiempo a descubrir este proyecto.

Espero de corazón que lo disfrutes tanto como yo he disfrutado construyéndolo.

**Nos vemos en la próxima partida.**

</td>

<td width="50%" valign="top">

## 🇬🇧

If you've made it this far, chances are we share the same passion.

I'd like to finish this README with a few personal words.

Due to health reasons, this will most likely be the last major software project I'll be able to build. After spending a large part of my professional life developing software, I've had to accept that my journey will take a different path much sooner than I ever expected.

I wanted to say goodbye to this chapter by creating something that brought together the two things I've loved the most throughout my life: programming and **Magic: The Gathering**, a game that has been with me for as long as I can remember and has always meant far more than just a game.

MagicAI was born from a simple idea: to build the tool I always wished I had, one that could help me understand the rules, organize my thoughts and continue enjoying this incredible game.

As long as my health allows it, I'll continue improving it little by little, learning and adding new features whenever I can.

If this project helps even a single player solve a rules question, discover a new interaction or simply enjoy Magic a little bit more, then it will have achieved everything I hoped for.

Thank you for taking the time to discover this project.

I truly hope you enjoy using it as much as I've enjoyed building it.

**See you in the next game.**

</td>

</tr>
</table>

---

### 🧙 **More Gathering. Less Guessing.**

</div>