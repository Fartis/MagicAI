# 🧙 MagicAI - More Gathering. Less Guessing.

"Porque preguntarle a un LLM genérico cómo funciona una interacción de Magic está bien... pero construir uno que consulte las reglas oficiales, recuerde el contexto de la conversación y funcione completamente en local es mucho más divertido."

> **Una IA especializada en Magic: The Gathering, ejecutándose completamente en local.**

MagicAI es un asistente conversacional diseñado para responder preguntas sobre **Magic: The Gathering** utilizando exclusivamente información oficial del juego.

En lugar de depender únicamente del conocimiento del modelo LLM, MagicAI construye dinámicamente un contexto utilizando:

- 📖 Oracle oficial de Scryfall
- 📚 Magic Comprehensive Rules
- 💬 Contexto de la conversación
- 🧠 Recuperación inteligente de cartas y reglas

Todo ello ejecutándose **100% en local** mediante **Ollama**, sin necesidad de utilizar APIs externas de IA.

---

# ✨ Características

- 🎴 Reconocimiento automático de cartas
- 📚 Consulta de reglas oficiales
- 💬 Conversaciones con memoria de contexto
- 🔎 Recuperación automática de cartas previamente mencionadas
- ⚡ Ejecución completamente local mediante Ollama
- 🖥️ Compatible con CPU y GPU (CUDA)
- 🧪 Suite de regresión para evitar romper funcionalidades existentes
- 📈 Test de rendimiento integrado

---

# 🏗 Arquitectura

```
                Usuario
                   │
                   ▼
            MagicAI Assistant
                   │
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
 Context Builder         Context Enricher
      │                         │
      └────────────┬────────────┘
                   ▼
          Knowledge Builder
                   │
                   ▼
              Ollama (LLM)
                   │
                   ▼
               Respuesta
```

---

# 📚 Fuentes de conocimiento

MagicAI utiliza exclusivamente información oficial:

- Oracle Cards (Scryfall)
- Comprehensive Rules
- Contexto de la conversación

El modelo de lenguaje **no necesita memorizar Magic**.

Su función es únicamente interpretar el conocimiento proporcionado.

---

# 🚀 Tecnologías utilizadas

- Python 3.12
- Ollama
- Qwen3 8B
- FastAPI
- Uvicorn

---

# 📁 Organización del proyecto

```
magicai/
│
├── assistant/
├── api/
├── conversation/
├── extractors/
├── llm/
├── repositories/
├── services/
│
tests/
│
├── regression/
└── test_performance.py
```

---

# 🧪 Testing

MagicAI incorpora dos tipos de pruebas.

## Regression Suite

Comprueba que la IA sigue respondiendo correctamente después de cada cambio.

Actualmente incluye escenarios como:

- Young Wolf
- Undying
- Persist
- Prossh
- Korvold
- Comparaciones
- Conversaciones largas
- Contexto implícito

## Performance Suite

Mide:

- Context Builder
- Context Enricher
- Knowledge Builder
- Tiempo de inferencia del LLM

---

# 📊 Estado actual

## ✅ Funcional

- Conversaciones persistentes
- Contexto automático
- Oracle oficial
- Comprehensive Rules
- Integración con Ollama
- GPU Support
- API REST
- Regression Suite
- Performance Suite

---

## 🚧 Próximas mejoras

- [ ] Card Index para acelerar búsquedas
- [ ] Sistema de caché
- [ ] Comparación automática entre cartas
- [ ] Resolución de ambigüedades (Carta vs Keyword)
- [ ] Streaming de respuestas
- [ ] Frontend estilo ChatGPT
- [ ] Benchmark avanzado
- [ ] Múltiples modelos LLM

---

# 🎯 Objetivo del proyecto

MagicAI **no pretende competir con ChatGPT**.

Su objetivo es construir un asistente especializado en Magic capaz de responder utilizando información oficial, manteniendo el contexto de una conversación y ejecutándose completamente en local.

---

# 📈 Estado del proyecto

**Versión:** `v0.1.0-alpha`

## Estado

🟢 Alpha funcional

### Actualmente

- ✅ Arquitectura estable
- ✅ 25 preguntas de regresión superadas
- ✅ 0 errores
- ✅ Ejecución acelerada mediante GPU
- ✅ Tiempo medio de respuesta ~6 segundos (RTX 4060 Ti)

---

# ❤️ Proyecto personal

MagicAI nace como un proyecto personal para experimentar con:

- Retrieval Augmented Generation (RAG)
- LLMs locales
- Arquitectura de asistentes conversacionales
- Ingeniería de contexto
- Optimización de rendimiento
- Testing de modelos conversacionales

Cada nueva versión busca acercar un poco más el comportamiento de un juez experto de Magic al de una IA ejecutándose íntegramente en local.

---

# 🃏 IABuilding your deck.

Deckbuilding has always been one of my favourite parts of Magic.

Building an AI turned out to be surprisingly similar.

You start with an idea.

You test.

You tune.

You remove what doesn't work.

You improve what does.

Then you shuffle up and try again.

Thank you for helping build this deck.

---

"Magic isn't just played. It's understood."

MagicAI exists to help you discover the magic hidden between the rules.