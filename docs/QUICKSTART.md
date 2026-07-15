# MagicAI quick start

## Stable branch

```bash
git clone https://github.com/Fartis/MagicAI.git
cd MagicAI
```

## Active development branch

```bash
git clone -b develop https://github.com/Fartis/MagicAI.git
cd MagicAI
```

## Python environment

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

## Local sources

```bash
./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py
```

## Ollama on the same machine

```bash
ollama pull qwen3:8b
export OLLAMA_URL=http://127.0.0.1:11434/api/chat
```

## Ollama in an existing container

```bash
docker exec ollama ollama pull qwen3:8b
export OLLAMA_URL=http://127.0.0.1:11434/api/chat
```

## Ollama on another LAN machine

```bash
export OLLAMA_URL=http://192.168.1.50:11434/api/chat
```

Use only a trusted local network. Do not expose an unprotected Ollama endpoint to the public Internet.

## Start MagicAI

```bash
python -m uvicorn magicai.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/ui
```

## Smoke test

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What happens if I sacrifice Young Wolf?"}'
```
