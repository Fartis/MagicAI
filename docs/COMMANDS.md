MagicAI Cheat Sheet

Activar entorno
---------------
source .venv/bin/activate

API
---
uvicorn magicai.api:app --reload

Swagger
--------
http://127.0.0.1:8000/docs

Performance
-----------
python tests/test_performance.py

Regresión
----------
python tests/regression/regression_test.py

Ollama
-------
ollama ps
ollama list

Git
---
git add .
git commit -m "..."
git tag v0.1.0-alpha

## Dynamic Gauntlet

Lista los conceptos dinámicos disponibles:

```bash
python -m tests.quality.dynamic_gauntlet_test --list-concepts
```

Genera y ejecuta 30 escenarios reproducibles desde el Oracle local:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 30
```

Restringe la ejecución a uno o varios conceptos:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --seed 184729 \
  --cases 12 \
  --concept mana_ability \
  --concept ward
```

Reproduce exactamente un fallo guardado:

```bash
python -m tests.quality.dynamic_gauntlet_test \
  --replay resultado_dynamic_gauntlet_failures/184729_DG-001_mana_ability.json
```

El manifiesto JSON conserva la semilla, carta, plantilla, pregunta, contrato de
validación y evidencia Oracle de cada escenario generado.
