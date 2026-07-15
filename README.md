<div align="center">

<img src="sources/logo.png" alt="MagicAI" width="420">

# MagicAI

### More Gathering. Less Guessing.

**Local, source-grounded assistant for Magic: The Gathering**

`v0.1.0-alpha` · Local-first · Python + Ollama

**Next public milestone:** `0.1 beta` — **Ponder**  
**Planned 1.0 codename:** **NicolAI Bolas**

</div>

---

## What is MagicAI?

MagicAI is a local AI project for **Magic: The Gathering**. Its factual core is the **Judge**, which retrieves Oracle text, Comprehensive Rules, rulings, and conversation context before answering.

> The model is not the source of truth. The Judge retrieves and validates evidence; language models explain it.

MagicAI does not attempt to memorize every card or rule. It builds the evidence required for each question, uses deterministic renderers when a formal answer is covered, validates model output, and falls back safely when the evidence is insufficient.

The second profile is the **Tactician**—shown as **Estratega** in the local UI. The Tactician analyzes game lines, interactions, synergies, and combos, but all factual data still passes through the Judge-owned source gateway.

## Current capabilities

- Local Scryfall Oracle and rulings snapshots.
- Local Magic Comprehensive Rules.
- Card, keyword, symbol, action, and rule retrieval.
- Conversation continuity and card disambiguation.
- Deterministic answers for covered rule families.
- Ollama fallback for explanations outside deterministic coverage.
- Source-grounded validation, retries, and safe fallback.
- Structured `JudgeResult` evidence and provenance.
- Local FastAPI REST API and browser UI.
- Persistent local conversation history in SQLite.
- Exportable community-feedback cases for evaluation only.
- Reproducible Gauntlets, multi-seed campaigns, process workers, sharding, and resume support.
- Tactician review of Judge contradictions.
- Automatic Judge-to-Tactician handoff for strategic questions.
- Referential follow-up support, including cards inherited from the previous turn.
- Initial generic combo reconstruction for sacrifice, Undying, counter-removal, token, and mana loops.

## Card scope

The standard Judge and evaluation catalog focus on ordinary paper cards. Funny, silver-border, acorn, and playtest cards are excluded, together with supplemental objects such as Vanguard cards, tokens, emblems, planes, phenomena, and schemes. Ordinary paper cards remain queryable even when they are currently banned.

## Development status

MagicAI is an advanced Judge alpha and an early integrated Tactician alpha. The quality infrastructure is mature enough to expose semantic false positives instead of merely checking surface matches, but arbitrary Magic interactions are not yet fully covered.

The latest focused C1.4 validation recorded:

```text
Focused and expanded tests      231/231
Full-Oracle smoke                 42/42
C1.3 finding replays              23/23
Rebuilt campaign               1,000/1,000
WARN                                   0
FAIL                                   0
```

These results describe a controlled and reproducible matrix. They do **not** mean every Magic card, rule, or interaction is covered.

The current Tactician milestone adds:

```text
Automatic strategic handoff
Conversation-card inheritance
Intent-specific strategy routing
Generic three-piece Undying loop detection
Judge capability registry
Structured combo steps and outcomes
```

See [docs/STATUS.md](docs/STATUS.md) for the current snapshot and [docs/ROADMAP.md](docs/ROADMAP.md) for the path to **Ponder**.

---

## Project principles

- **Judge authority:** the Judge is the sole factual authority for Oracle text, rules, rulings, and legality.
- **Tactician autonomy:** the Tactician may investigate iteratively and request as many Judge-owned tools as needed.
- **Source gateway:** strategic profiles never open factual sources directly.
- **Retrieve, do not memorize:** current sources take precedence over model memory.
- **No card-specific patches:** fixes must be generic, inspectable, and reusable.
- **Local-first:** inference runs through Ollama on the user's machine.
- **Safe uncertainty:** insufficient evidence is better than invented certainty.
- **Test the premise:** a correct answer is useless when the generated scenario is invalid.
- **Evaluation is not training:** reports and feedback artifacts never modify model weights automatically.

See [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md).

---

## Architecture overview

```text
User / API / UI
       │
       ▼
Conversation and intent routing
       │
       ├──────── factual question ───────► Judge
       │                                      │
       │                                      ├─ Oracle / Scryfall rulings
       │                                      ├─ Comprehensive Rules
       │                                      ├─ symbology / legality
       │                                      └─ deterministic validation
       │
       └──────── strategic question ─────► automatic handoff
                                              │
                                              ▼
                                        Tactician
                                     plan / combo / line
                                              │
                                              ▼
                                    Judge source gateway
                                              │
                                              ▼
                                  challenge / verify / critic
                                              │
                                              ▼
                                         final answer
```

The Tactician may make repeated structured requests through the Judge. The source boundary is a trust boundary, not an intelligence limit.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/TACTICIAN.md](docs/TACTICIAN.md).

---

## Requirements

- Python **3.12+**
- Ollama reachable over HTTP
- Recommended model: **Qwen3 8B**
- `curl`, `wget`, and `jq` for source download scripts
- Linux, WSL2, or an equivalent environment

Default environment:

```text
OLLAMA_URL=http://127.0.0.1:11434/api/chat
MAGICAI_MODEL=qwen3:8b
```

---

## Quick start

```bash
git clone https://github.com/Fartis/MagicAI.git
cd MagicAI

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

./scripts/download_sources.sh
./scripts/download_rules.sh
python scripts/update_scryfall_symbology.py

ollama pull qwen3:8b
python -m uvicorn magicai.api:app --reload
```

Open:

```text
UI    http://127.0.0.1:8000/ui
API   http://127.0.0.1:8000/docs
```

The complete setup guide, including `main` versus `develop`, Docker Ollama, and LAN Ollama, is in [docs/QUICKSTART.md](docs/QUICKSTART.md).

---

## API profiles

```text
POST /ask             Judge entry point with automatic strategic handoff
POST /tactician/ask   Explicit Tactician entry point
GET  /meta            contracts, profiles, codenames, and Judge capabilities
GET  /health          source and service health
```

Automatic handoff can be disabled for diagnostic clients:

```json
{
  "question": "Do these cards form a combo?",
  "auto_handoff": false
}
```

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) and [docs/JUDGE_RESULT.md](docs/JUDGE_RESULT.md).

---

## Testing

Focused deterministic tests:

```bash
PYTHONPATH=. python -m tests.validation.rule_renderer_test
PYTHONPATH=. python -m tests.validation.oracle_renderer_test
PYTHONPATH=. python -m tests.tactician.tactician_reviewer_test
PYTHONPATH=. python -m tests.tactician.tactician_strategy_test
PYTHONPATH=. python -m tests.tactician.tactician_conversation_handoff_test
```

Exhaustive Oracle evaluation:

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir quality-results/oracle-exhaustive
```

See [docs/COMMANDS.md](docs/COMMANDS.md) and [docs/DEV_COMMANDS.md](docs/DEV_COMMANDS.md).

---

## Main structure

```text
MagicAI/
├── magicai/
│   ├── api/               # REST API
│   ├── assistant/         # Judge orchestration
│   ├── conversation/      # sessions and continuity
│   ├── judge_tools/       # Judge-owned capability registry
│   ├── retrieval/         # rule and Oracle query construction
│   ├── tactician/         # strategic analysis and challenges
│   ├── validation/        # renderers, validation, and fallback
│   └── ui/                # local browser UI
├── tests/
├── docs/
├── scripts/
├── sources/
└── database/
```

---

## Release names

- **0.1 beta — Ponder:** the first integrated Judge + Tactician beta.
- **1.0 — NicolAI Bolas:** the planned complete first major release.

The codenames do not change MagicAI's source-grounded architecture or licensing.

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Quick start](docs/QUICKSTART.md)
- [Commands](docs/COMMANDS.md)
- [Developer commands](docs/DEV_COMMANDS.md)
- [UI](docs/UI.md)
- [Current status](docs/STATUS.md)
- [JudgeResult](docs/JUDGE_RESULT.md)
- [API contract](docs/API_CONTRACT.md)
- [Roadmap](docs/ROADMAP.md)
- [Tactician](docs/TACTICIAN.md)
- [Philosophy](docs/PHILOSOPHY.md)
- [Contributing](docs/CONTRIBUTING.md)

---

## License

MagicAI is distributed under the **GNU Affero General Public License v3.0 or later** (`AGPL-3.0-or-later`). See [LICENSE](LICENSE) and [docs/LICENSING.md](docs/LICENSING.md).

---

# ❤️ A personal letter

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

____

Si has llegado hasta aquí, lo más probable es que compartamos la misma pasión.

Me gustaría terminar este archivo README con unas palabras personales.

Por motivos de salud, es muy probable que este sea el último gran proyecto de software que pueda desarrollar. Después de dedicar gran parte de mi vida profesional al desarrollo de software, he tenido que aceptar que mi trayectoria tomará un rumbo diferente mucho antes de lo que jamás hubiera imaginado.

Quería despedirme de este capítulo creando algo que reuniera las dos cosas que más he amado a lo largo de mi vida: la programación y **Magic: The Gathering**, un juego que me ha acompañado desde que tengo uso de razón y que siempre ha significado mucho más que un simple juego.

MagicAI nació de una idea sencilla: crear la herramienta que siempre había deseado tener, una que me ayudara a entender las reglas, a organizar mis ideas y a seguir disfrutando de este increíble juego.

Mientras mi salud me lo permita, seguiré mejorándola poco a poco, aprendiendo y añadiendo nuevas funciones siempre que pueda.

Si este proyecto ayuda aunque sea a un solo jugador a resolver una duda sobre las reglas, a descubrir una nueva interacción o, simplemente, a disfrutar un poco más de Magic, habrá logrado todo lo que esperaba.

Gracias por dedicar tu tiempo a descubrir este proyecto.

Espero de verdad que disfrutes usándolo tanto como yo he disfrutado creándolo.

**Nos vemos en la próxima partida.**

---

<div align="center">

### 🧙 More Gathering. Less Guessing.

</div>
