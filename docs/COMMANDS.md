# 🧰 Comandos de MagicAI

> Referencia operativa para desarrollo, fuentes, API, pruebas, campañas y Git.

[Entorno](#-entorno) · [Fuentes](#-fuentes-locales) · [Ollama](#-ollama) · [API](#-api-rest) · [Tests](#-pruebas) · [Git](#-git) · [English](#-english-quick-reference)

---

## 🐍 Entorno

Crear y activar el entorno:

```bash
cd ~/MagicAI
python3.12 -m venv .venv
source .venv/bin/activate
```

Instalar MagicAI en modo editable y resolver sus dependencias declaradas en `pyproject.toml`:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Instalar usando exactamente las versiones validadas del lock:

```bash
python -m pip install -r requirements.txt   -c requirements.lock.txt
```

`requirements.txt` contiene `-e .`; no es necesario ejecutar además `pip install -e .`.

Comprobar instalación y dependencias:

```bash
python --version
python -m pip check
python -m pip show magicai
python -c "import magicai; print('MagicAI import OK:', magicai.__file__)"
```

En `python -m pip show magicai`, el campo `Requires` debe incluir:

```text
fastapi, pydantic, requests, uvicorn
```

Prueba reproducible desde un entorno vacío:

```bash
cd ~/MagicAI
rm -rf /tmp/magicai-clean-venv
python3.12 -m venv /tmp/magicai-clean-venv
source /tmp/magicai-clean-venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt   -c requirements.lock.txt
python -m pip check
python -m pip show magicai

python - <<'PY'
import fastapi
import magicai
import pydantic
import requests
import uvicorn

print("MagicAI:", magicai.__file__)
print("FastAPI:", fastapi.__version__)
print("Pydantic:", pydantic.__version__)
print("Requests:", requests.__version__)
print("Uvicorn:", uvicorn.__version__)
PY

deactivate
rm -rf /tmp/magicai-clean-venv
```

Salir del entorno:

```bash
deactivate
```

---

## 📚 Fuentes locales

Descargar los bulk Oracle y rulings utilizados por el Juez:

```bash
./scripts/download_sources.sh
```

Descargar la última versión disponible de Comprehensive Rules:

```bash
./scripts/download_rules.sh
```

Actualizar símbolos de Scryfall:

```bash
python scripts/update_scryfall_symbology.py
```

Comprobar ficheros:

```bash
ls -lh sources/scryfall/oracle-cards.json
ls -lh sources/scryfall/rulings.json
ls -lh sources/scryfall/symbology.json
ls -lh sources/rules/MagicCompRules.txt
```

Explorar la primera entrada del bulk Oracle:

```bash
python scripts/explore_scryfall.py
```

Los bulk JSON, informes y bases locales están excluidos de Git.

---

## 🤖 Ollama

Variables por defecto:

```bash
export OLLAMA_URL=http://127.0.0.1:11434/api/chat
export MAGICAI_MODEL=qwen3:8b
```

Ollama instalado en el host:

```bash
ollama list
ollama ps
ollama pull qwen3:8b
```

Ollama en el contenedor `ollama`:

```bash
docker ps --filter name=ollama
docker exec ollama ollama list
docker exec ollama ollama ps
docker exec ollama ollama pull qwen3:8b
```

Comprobar la API:

```bash
curl http://127.0.0.1:11434/api/tags
```

---

## 🌐 API REST

Iniciar en desarrollo:

```bash
python -m uvicorn magicai.api:app --reload
```

Iniciar accesible desde la red local:

```bash
python -m uvicorn magicai.api:app \
  --host 0.0.0.0 \
  --port 8000
```

Rutas:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/meta
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

Pregunta nueva:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Puedo responder a Ward?"}'
```

Continuar una conversación:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"ID_DEVUELTO_POR_LA_PRIMERA_PREGUNTA",
    "question":"¿Y si destruyen la fuente?"
  }'
```

La respuesta mantiene `answer` y `session_id`, y añade el contrato `JudgeResult`. Para inspeccionarlo:

```bash
curl -sS http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Puedo responder durante la resolución?"}' |
  jq '{answer, status, origin, confidence, authority, cards, rules, warnings, source_versions}'
```

Estados actuales:

```text
answered
needs_clarification
insufficient_evidence
strategy_required
false_premise
```

Consultar versiones y enums admitidos:

```bash
curl -sS http://127.0.0.1:8000/meta | jq
```

Comprobar fuentes y Ollama:

```bash
curl -sS http://127.0.0.1:8000/health | jq
```

`ready=true` indica que Oracle y Comprehensive Rules están disponibles.
`full_service=true` indica además que Ollama y el modelo configurado responden.

Comprobar el error estructurado para una pregunta vacía:

```bash
curl -sS -i http://127.0.0.1:8000/ask   -H 'Content-Type: application/json'   -d '{"question":"   "}'
```

---

## 🔎 Herramientas de diagnóstico

Buscar una carta:

```bash
python scripts/search_card.py "Young Wolf"
```

Buscar una regla:

```bash
python scripts/search_rule.py "Undying"
```

Crear la base SQLite experimental:

```bash
python scripts/build_database.py
```

La base SQLite todavía no forma parte del pipeline principal del Juez.

---

## 🧪 Pruebas

### Compilación y formato del diff

```bash
python -m compileall -q magicai tests
git diff --check
```

### Suite rápida recomendada

```bash
PYTHONPATH=. python -m tests.quality.dynamic_gauntlet_generator_test
PYTHONPATH=. python -m tests.quality.dynamic_campaign_planner_test
PYTHONPATH=. python -m tests.quality.dynamic_concept_contract_test
PYTHONPATH=. python -m tests.retrieval.rule_queries_test
PYTHONPATH=. python -m tests.retrieval.rule_intent_test
PYTHONPATH=. python -m tests.retrieval.card_extractor_test
PYTHONPATH=. python -m tests.retrieval.card_scope_test
PYTHONPATH=. python -m tests.retrieval.context_enricher_test
PYTHONPATH=. python -m tests.retrieval.conversation_continuity_test
PYTHONPATH=. python -m tests.validation.rule_renderer_test
PYTHONPATH=. python -m tests.validation.oracle_renderer_test
PYTHONPATH=. python -m tests.quality.gauntlet_matcher_test
PYTHONPATH=. python -m tests.quality.open_judge_contract_test
PYTHONPATH=. python -m tests.quality.open_judge_evaluator_test
PYTHONPATH=. python -m tests.quality.open_judge_reports_test
PYTHONPATH=. python -m tests.validation.strategy_boundary_test
PYTHONPATH=. python -m tests.validation.judge_result_test
PYTHONPATH=. python -m tests.api.judge_result_schema_test
PYTHONPATH=. python -m tests.retrieval.source_versions_test
PYTHONPATH=. python -m tests.retrieval.rulings_source_test
PYTHONPATH=. python -m tests.retrieval.rulings_pipeline_test
PYTHONPATH=. python -m tests.validation.premise_guard_test
PYTHONPATH=. python -m tests.validation.assumptions_test
```

### API

```bash
PYTHONPATH=. python -m tests.api.api_smoke_test
PYTHONPATH=. python -m tests.api.api_ambiguity_test
```

### Regression Suite

```bash
PYTHONPATH=. python -m tests.regression.regression_test
```

Paralela:

```bash
PYTHONPATH=. python -m tests.regression.regression_parallel
```

### Open Judge Gauntlet

Validar contratos y evaluador sin Ollama:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_contract_test
PYTHONPATH=. python -m tests.quality.open_judge_evaluator_test
PYTHONPATH=. python -m tests.quality.open_judge_reports_test
PYTHONPATH=. python -m tests.validation.strategy_boundary_test
PYTHONPATH=. python -m tests.validation.judge_result_test
PYTHONPATH=. python -m tests.api.judge_result_schema_test
PYTHONPATH=. python -m tests.retrieval.source_versions_test
PYTHONPATH=. python -m tests.retrieval.rulings_source_test
PYTHONPATH=. python -m tests.retrieval.rulings_pipeline_test
PYTHONPATH=. python -m tests.validation.premise_guard_test
PYTHONPATH=. python -m tests.validation.assumptions_test
```

Listar conversaciones:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_test --list-cases
```

Ejecutar la baseline completa:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_test
```

Ejecutar solo casos concretos:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_test \
  --case OJ-002 \
  --case OJ-003 \
  --case OJ-006 \
  --case OJ-007 \
  --case OJ-008
```

Estos casos concentran el hardening de continuidad, keywords, reglas referenciadas, comparaciones y procedimientos. `OJ-010` valida que Squee pida desambiguación solo entre cartas jugables.

Por defecto, la baseline genera informes aunque existan fallos semánticos. Para usarla como puerta de calidad:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_test --fail-on-critical
PYTHONPATH=. python -m tests.quality.open_judge_test --strict
```

Salida:

```text
resultado_open_judge/<run-id>/
├── open_judge_summary.txt
├── open_judge_summary.json
├── open_judge_summary.xml
├── open_judge_summary.html
└── open_judge_failures/
```

### Performance

```bash
PYTHONPATH=. python -m tests.test_performance
```

### Reddit Gauntlet

```bash
PYTHONPATH=. python -m tests.quality.reddit_gauntlet_test
```

### Estabilidad Open Judge para Release Candidate

Después de generar tres baselines completas:

```bash
PYTHONPATH=. python -m tests.quality.open_judge_stability_test   resultado_open_judge/RUN_1   resultado_open_judge/RUN_2   resultado_open_judge/RUN_3
```

La puerta exige el mismo número de casos y turnos y rechaza cualquier resultado fuera de:

```text
PASS
FALSE_PREMISE_HANDLED
NEEDS_CLARIFICATION
STRATEGY_REQUIRED
```

### Generalization Probe

```bash
PYTHONPATH=. python -m tests.quality.generalization_probe_test
```

Las suites anteriores pueden requerir Oracle, reglas y Ollama.

---

## 🎲 Dynamic Gauntlet

Listar conceptos:

```bash
python -m tests.quality.dynamic_gauntlet_test --list-concepts
```

Ejecutar 42 escenarios reproducibles:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 42
```

Restringir conceptos:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 9 \
  --concept mana_ability \
  --concept ward \
  --concept source_independence
```

Solo conceptos basados en reglas:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 12 \
  --concept cleanup_priority \
  --concept commander_copy \
  --concept persist \
  --concept counter_replacement_order
```

Parar en el primer FAIL:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 42 \
  --fail-fast
```

Reproducir un fallo guardado:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --replay resultado_dynamic_gauntlet_failures/SEED_CASO_CONCEPTO.json
```

Archivos generados por defecto:

```text
resultado_dynamic_gauntlet.txt
resultado_dynamic_gauntlet.xml
resultado_dynamic_gauntlet.html
resultado_dynamic_gauntlet_manifest.json
resultado_dynamic_gauntlet_failures/
```

---

## 🧭 Campaña multisemilla

Semillas explícitas:

```bash
python -m tests.quality.dynamic_campaign_test \
  --seed 184729 \
  --seed 987654 \
  --seed 424242 \
  --cases 42 \
  --require-full-coverage \
  --fail-on-warn
```

Semillas derivadas desde una base:

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 184729 \
  --runs 5 \
  --cases 42 \
  --require-full-coverage
```

Salida:

```text
resultado_dynamic_campaign/
├── campaign_summary.json
├── campaign_summary.txt
├── campaign_summary.html
├── run_01_seed_.../
├── run_02_seed_.../
└── run_03_seed_.../
```

Limpiar resultados:

```bash
rm -rf \
  resultado_dynamic_gauntlet.txt \
  resultado_dynamic_gauntlet.xml \
  resultado_dynamic_gauntlet.html \
  resultado_dynamic_gauntlet_manifest.json \
  resultado_dynamic_gauntlet_failures \
  resultado_dynamic_campaign
```

---

## 🗄️ Backup

Crear backup:

```bash
./tools/backup.sh
```

Cambiar el directorio de destino:

```bash
MAGICAI_BACKUP_ROOT=/ruta/de/backups ./tools/backup.sh
```

---

## 🌿 Git

Actualizar `develop`:

```bash
git switch develop
git pull --ff-only origin develop
```

Crear una rama:

```bash
git switch -c feature/nombre-corto
```

Revisar cambios:

```bash
git status --short
git diff --stat
git diff --check
```

Commit y push:

```bash
git add -A
git commit -m "Descripción del cambio"
git push -u origin "$(git branch --show-current)"
```

Aplicar un parche:

```bash
git apply --check ~/cambio.patch
git apply ~/cambio.patch
```

Revertir un parche no confirmado:

```bash
git apply -R ~/cambio.patch
```

Guardar cambios temporales:

```bash
git stash push -u -m "descripcion"
git stash list
git stash pop
```

---

## 🇬🇧 English quick reference

The commands above are directly usable regardless of language. The usual workflow is:

```bash
source .venv/bin/activate
./scripts/download_sources.sh
./scripts/download_rules.sh
python -m uvicorn magicai.api:app --reload
```

Run the fast validation set before committing, then execute a 42-case Dynamic Gauntlet or a multiseed campaign for changes that affect retrieval, selection, rendering or evaluation.
