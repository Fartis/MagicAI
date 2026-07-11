# 🧙 Filosofía de MagicAI

> More Gathering. Less Guessing.

[Español](#-por-qué-existe-magicai) · [English](#-philosophy-summary)

---

## 🇪🇸 Por qué existe MagicAI

Los modelos de lenguaje explican muy bien, pero no deben considerarse una fuente oficial de Magic. Sus datos pueden estar incompletos, desactualizados o mezclados con texto impreso antiguo, rulings históricos y patrones aprendidos sin contexto.

MagicAI parte de una decisión distinta:

> Recuperar primero. Razonar después. Explicar al final.

El objetivo no es construir un chatbot que suene seguro. Es construir una herramienta local que pueda mostrar de dónde sale una respuesta y que sepa detenerse cuando no dispone de evidencia suficiente.

---

## El Juez como autoridad factual

El Juez es la única autoridad factual de MagicAI para:

- texto Oracle;
- características de cartas;
- reglas;
- rulings;
- legalidad;
- identidad de color;
- resultado reglamentario de una interacción.

El LLM no “sabe” estas cosas dentro de la arquitectura. Solo explica evidencia recuperada.

Los futuros Deck Master y Deckbuilder no tendrán una vía alternativa. Cuando necesiten verificar una carta o interacción, deberán preguntárselo al Juez.

---

## Retrieve, do not memorize

MagicAI no intenta introducir todo Magic en un prompt ni entrenar al modelo para recordar el juego completo.

```text
Carta mencionada
    → recuperar Oracle

Mecánica detectada
    → recuperar reglas

Pregunta ambigua
    → pedir aclaración

Evidencia insuficiente
    → reconocer el límite
```

Cuanto menos tenga que imaginar el modelo, menor será la superficie de alucinación.

---

## Ingeniería antes que prompting

Los problemas deben resolverse en la capa correcta:

- una carta equivocada se corrige en el selector;
- una regla ausente se corrige en retrieval;
- una premisa falsa se corrige en el generador;
- una respuesta formal repetible puede convertirse en renderer;
- una contradicción se captura en validación;
- una ambigüedad se gestiona en conversación.

Añadir una frase al prompt es la última opción, no la primera.

---

## No hardcodes de cartas

Un test puede revelar el problema, pero no define la solución.

No se debe arreglar “Sol Ring”, “Young Wolf” o una frase exacta. Debe arreglarse la categoría general:

```text
habilidades de maná
keywords intrínsecas
fuentes separadas de habilidades en la pila
cambios de zona de comandantes
efectos de reemplazo concurrentes
```

Un fix correcto debe mejorar preguntas nuevas que no existían cuando se escribió.

---

## Una respuesta correcta no basta

MagicAI también audita la premisa.

Una explicación correcta sobre Undying sigue siendo un fallo si la carta seleccionada no tiene Undying. Por eso los escenarios dinámicos conservan Oracle, tipo, set, legalidad y selector utilizado.

La calidad se evalúa en dos niveles:

```text
Premisa válida
    +
Respuesta correcta y respaldada
    =
PASS real
```

---

## Incertidumbre segura

El Juez debe diferenciar:

- sé la respuesta y tengo evidencia;
- necesito una aclaración;
- la premisa es falsa;
- la evidencia recuperada no basta.

Responder “no puedo determinarlo con seguridad” puede ser un fallo de retrieval que haya que corregir, pero sigue siendo preferible a inventar.

---

## Alcance pragmático

MagicAI prioriza casos reales de jugadores y formatos oficiales. Las cartas de broma, silver-border, acorn y playtest quedan fuera del catálogo estándar.

No se pretende gastar desarrollo o computación en escenarios extremadamente marginales mientras falten familias de reglas utilizadas a diario.

Esto no impide crear en el futuro un modo experimental separado. Simplemente evita que ese contenido contamine el núcleo del producto.

---

## Local-first

La inferencia se ejecuta en local mediante Ollama. Las preguntas y conversaciones no necesitan enviarse a un proveedor de IA externo.

Las fuentes pueden actualizarse mediante Internet, pero el flujo normal de respuesta utiliza los ficheros locales preparados por el usuario.

---

## Enseñar, no solo contestar

El Juez debe dar respuestas comprensibles y suficientemente precisas para que el jugador pueda reconocer el patrón en futuras partidas.

Después, Deck Master ayudará a valorar y jugar mazos, y Deckbuilder ayudará a construirlos o mejorarlos. Ninguno sustituirá al Juez: lo utilizarán como base factual.

---

## 🇬🇧 Philosophy summary

MagicAI retrieves before it explains. The language model is not the authority; the Judge is. Card text, rules, rulings and legality must come from retrieved sources, while uncertainty and false premises must be represented explicitly.

Engineering fixes belong in selectors, retrieval, renderers, validation or conversation handling—not in card-specific prompt patches. Future strategic profiles will remain dependent on the Judge for every factual Magic claim.
