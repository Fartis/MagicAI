# MagicAI Quickstart

Esta guía lleva desde un clon limpio hasta la UI local del Juez.

## Elegir rama

Para usar la versión estable publicada:

```bash
git clone https://github.com/Fartis/MagicAI.git
cd MagicAI
```

Para probar o contribuir al desarrollo activo:

```bash
git clone -b develop https://github.com/Fartis/MagicAI.git
cd MagicAI
```

`main` contiene la versión estable o publicada. `develop` integra el trabajo activo y las ramas `feature/*` aíslan cada sprint.

## Preparar Python

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Para reproducir las versiones validadas:

```bash
python -m pip install -r requirements.txt -c requirements.lock.txt
```

## Descargar fuentes locales

```bash
./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py
```

Comprueba que existen:

```bash
ls -lh sources/scryfall/oracle-cards.json
ls -lh sources/scryfall/rulings.json
ls -lh sources/scryfall/symbology.json
ls -lh sources/rules/MagicCompRules.txt
```

## Preparar Ollama

### Ollama en el mismo equipo

```bash
ollama pull qwen3:8b
export OLLAMA_URL=http://127.0.0.1:11434/api/chat
export MAGICAI_MODEL=qwen3:8b
```

### Ollama en un contenedor existente

```bash
docker exec ollama ollama pull qwen3:8b
export OLLAMA_URL=http://127.0.0.1:11434/api/chat
export MAGICAI_MODEL=qwen3:8b
```

### Ollama en otra máquina de la red local

```bash
export OLLAMA_URL=http://IP_DEL_EQUIPO_OLLAMA:11434/api/chat
export MAGICAI_MODEL=qwen3:8b
```

La máquina que ejecuta Ollama debe aceptar conexiones desde el equipo de MagicAI. No expongas Ollama directamente a Internet sin una capa de seguridad adecuada.

## Iniciar MagicAI

```bash
python -m uvicorn magicai.api:app \
  --host 127.0.0.1 \
  --port 8000
```

Abre:

```text
http://127.0.0.1:8000/ui
```

La documentación interactiva de la API está en:

```text
http://127.0.0.1:8000/docs
```

## Verificar salud

```bash
curl -sS http://127.0.0.1:8000/health | jq
```

- `ready=true`: Oracle y Comprehensive Rules están disponibles.
- `full_service=true`: además Ollama y el modelo configurado responden.
- `status=degraded`: la UI puede conservar respuestas deterministas aunque falte un servicio auxiliar.

## Primera demostración

Prueba esta secuencia en la UI:

```text
¿Qué hace Young Wolf?
¿Y si lo sacrifico?
¿Y si lo exilio?
```

Para probar desambiguación interactiva:

```text
¿Qué hace la criatura goblin Squee?
```

Para probar trazabilidad y supuestos:

```text
¿Cuántos Kobolds crea Prossh, Skyraider of Kher?
```

## API mínima

```bash
curl -sS http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Puedo responder durante la resolución de una habilidad?"}' |
  jq '{answer, status, origin, confidence, cards, rules, assumptions, warnings}'
```

## Problemas frecuentes

### La UI abre, pero Ollama no responde

```bash
curl -sS http://127.0.0.1:11434/api/tags | jq
ollama list
```

Comprueba `OLLAMA_URL`, el modelo configurado y el endpoint `/health`.

### Faltan cartas o reglas

Repite:

```bash
./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py
```

### El historial no aparece

Las conversaciones se guardan en SQLite local y deberían sobrevivir al reinicio de FastAPI. Comprueba la ruta predeterminada `~/.local/share/magicai/conversations.sqlite3` o define `MAGICAI_CONVERSATION_DB`. `localStorage` solo conserva una copia rápida de la conversación activa.

## Siguiente documentación

- [UI beta](UI.md)
- [Comandos completos](COMMANDS.md)
- [Estado actual](STATUS.md)
- [Contrato HTTP](API_CONTRACT.md)
- [JudgeResult](JUDGE_RESULT.md)
