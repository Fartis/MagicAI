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