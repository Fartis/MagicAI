# ❤️ Contribuir a MagicAI

> Las contribuciones deben mejorar la generalización, la trazabilidad y la seguridad factual del Juez.

[Español](#-antes-de-empezar) · [English](#-contribution-summary)

---

## 🇪🇸 Antes de empezar

Lee:

- [PHILOSOPHY.md](PHILOSOPHY.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [STATUS.md](STATUS.md)
- [ROADMAP.md](ROADMAP.md)

MagicAI no es un chatbot generalista. El Juez es una autoridad factual source-grounded y la arquitectura protege esa frontera.

---

## Qué hace buena una contribución

Una contribución debería cumplir varias de estas propiedades:

- resuelve una categoría, no una carta concreta;
- añade o mejora evidencia recuperada;
- incluye una regresión reproducible;
- distingue premisa, retrieval, renderer y contrato;
- evita aumentar el prompt para ocultar un fallo de ingeniería;
- mantiene compatibilidad con manifiestos y replays cuando proceda;
- documenta cambios visibles para usuarios o colaboradores.

### Ejemplo correcto

Un caso sobre una carta revela que una keyword aparece en el nombre de otra habilidad. La solución endurece el detector de keywords intrínsecas y añade fixtures positivos y negativos.

### Ejemplo incorrecto

```python
if card.name == "La carta del test":
    return expected_answer
```

---

## Autoridad y acceso a fuentes

Solo el Juez debe actuar como autoridad factual sobre:

- cartas;
- Oracle;
- legalidad;
- reglas;
- rulings;
- identidad de color.

Los futuros perfiles no deben consultar esas fuentes directamente. Cualquier contribución a Deck Master o Deckbuilder deberá utilizar la interfaz del Juez.

---

## Alcance de cartas

Los tests estándar deben utilizar cartas de papel jugables en formatos oficiales soportados.

No añadas al catálogo normal:

- cartas `funny`;
- silver-border;
- acorn;
- playtest;
- objetos sin legalidad soportada.

Un modo experimental separado puede discutirse en el futuro, pero no debe contaminar las campañas principales.

---

## Preparar el entorno

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Descarga las fuentes necesarias:

```bash
./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py
```

---

## Flujo de ramas

Parte de `develop` actualizado:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/descripcion-corta
```

Antes de abrir una PR:

```bash
git status --short
git diff --check
python -m compileall -q magicai tests
```

Evita mezclar en el mismo commit:

- refactorizaciones masivas;
- cambios de comportamiento;
- actualización de fuentes;
- artefactos generados.

---

## Pruebas mínimas

Para cambios de retrieval o reglas:

```bash
PYTHONPATH=. python -m tests.retrieval.rule_queries_test
PYTHONPATH=. python -m tests.validation.rule_renderer_test
PYTHONPATH=. python -m tests.quality.dynamic_concept_contract_test
```

Para cambios del generador o catálogo:

```bash
PYTHONPATH=. python -m tests.quality.dynamic_gauntlet_generator_test
PYTHONPATH=. python -m tests.quality.dynamic_campaign_planner_test
```

Para cambios del pipeline:

```bash
PYTHONPATH=. python -m tests.quality.reddit_gauntlet_test
PYTHONPATH=. python -m tests.quality.generalization_probe_test
```

Las suites que consultan Ollama requieren el servicio y las fuentes locales disponibles.

---

## Cómo clasificar un fallo

Antes de modificar producción, identifica la categoría:

```text
false premise
selector failure
retrieval failure
routing failure
renderer failure
validator failure
contract mismatch
LLM generation failure
insufficient evidence handled correctly
```

No cambies el renderer para satisfacer una pregunta cuya premisa es falsa. No debilites un contrato correcto para convertir una respuesta incompleta en PASS.

---

## Tests dinámicos

Todo escenario dinámico debe conservar suficiente información para reproducirlo:

- seed;
- concepto;
- plantilla;
- pregunta;
- contrato;
- tipo de fuente;
- carta y Oracle cuando corresponda;
- set y formatos legales;
- fichero de fallo.

Un nuevo concepto debe incluir al menos varias paráfrasis controladas y tests de cobertura de retrieval.

---

## Estilo de código

- Python 3.12+.
- Funciones pequeñas y con responsabilidad clara.
- Nombres explícitos.
- Evita dependencias nuevas sin necesidad.
- No introduzcas acceso de red en el flujo normal de respuesta.
- Mantén las fuentes descargables y versionables por separado.
- Actualiza documentación y comandos cuando cambie una interfaz.

---

## Pull requests

Incluye:

1. problema observado;
2. causa raíz;
3. solución genérica;
4. tests añadidos;
5. resultados antes/después;
6. riesgos y compatibilidad;
7. documentación modificada.

No incluyas:

- bulk JSON de Scryfall;
- bases de datos locales;
- HTML/TXT/XML generados;
- ZIP de campañas;
- patches auxiliares;
- secretos o configuración personal.

---

## 🇬🇧 Contribution summary

Contributions should improve generalization, evidence quality and factual safety. Fix categories rather than individual cards, classify failures before changing production code and include reproducible tests.

The Judge remains the sole factual authority. Future strategic profiles must call the Judge instead of querying card or rules sources directly.
