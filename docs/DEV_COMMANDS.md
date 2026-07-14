# MagicAI — Comandos de desarrollo

Este documento reúne comandos operativos para desarrollo, diagnóstico y campañas de evaluación de gran tamaño.

No sustituye a `docs/COMMANDS.md`, que contiene los comandos generales del proyecto. Aquí se documentan procedimientos internos que pueden consumir horas, generar miles de resultados o producir artefactos temporales destinados a revisión técnica.

> **Principio del proyecto:** estos procesos evalúan el código del Juez. No entrenan el modelo, no generan datasets de aprendizaje, no modifican pesos y no promocionan resultados automáticamente.

---

## 1. Preparación común

Desde la raíz del repositorio:

```bash
cd ~/MagicAI
source .venv/bin/activate
export PYTHONPATH=.
```

Comprobar el estado de Git:

```bash
git status --short
git branch --show-current
git log -1 --oneline
```

Para campañas comparables y reproducibles se recomienda trabajar desde un commit conocido. Un árbol modificado no impide técnicamente la ejecución, pero debe quedar reflejado en la información de la campaña.

Comprobar Python y Ollama:

```bash
python --version
ollama --version
curl -fsS http://127.0.0.1:11434/api/tags >/dev/null \
  && echo "Ollama responde correctamente" \
  || echo "Ollama no responde en el puerto 11434"
```

Comprobar que el runner dinámico está disponible:

```bash
python -m tests.quality.dynamic_campaign_test --help
```

Listar los conceptos disponibles:

```bash
python -m tests.quality.dynamic_campaign_test --list-concepts
```

---

## 2. Diferencia entre los dos Gauntlets de desarrollo

### Dynamic Gauntlet

Genera automáticamente escenarios reproducibles a partir de:

- conceptos reglamentarios implementados en el generador;
- plantillas de preguntas;
- cartas obtenidas desde Oracle/Scryfall;
- una o varias semillas reproducibles.

Se utiliza para descubrir errores de generalización y someter al Juez a muchas combinaciones.

Comando principal:

```bash
python -m tests.quality.dynamic_campaign_test
```

### Community Feedback Gauntlet

Ejecuta casos JSON preparados manualmente o exportados desde la UI. Se utiliza para reproducir preguntas reales, parafraseadas y revisables.

Comando principal:

```bash
python -m tests.quality.community_feedback_test
```

El Dynamic Gauntlet dispone de:

```text
--workers
--resume
```

Cada worker es un **proceso independiente**, no un hilo de Python. Cada proceso ejecuta una semilla completa en su propio directorio y el resumen final se agrega en orden determinista.

El Community Feedback Gauntlet dispone además de:

```text
--campaign-id
--resume
--retry-errors
--checkpoint-every
```

El Dynamic Gauntlet y el Community Feedback Gauntlet no son sistemas de aprendizaje. Sus salidas son informes de evaluación.

---

## 3. Prueba corta antes de una campaña grande

Antes de dejar el PC trabajando durante horas, ejecutar una campaña corta de tres semillas y diez casos por semilla:

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 20260714 \
  --runs 3 \
  --cases 10 \
  --workers 1 \
  --output-dir quality-results/dynamic-smoke-30 \
  --require-full-coverage
```

El total será:

```text
3 ejecuciones × 10 casos = 30 casos
```

Que el comando termine con código `1` puede significar que encontró `FAIL`, advertencias sujetas a política o cobertura incompleta. No implica necesariamente que Python u Ollama se hayan bloqueado.

Consultar el resumen:

```bash
python -m json.tool \
  quality-results/dynamic-smoke-30/campaign_summary.json | less
```

Eliminar esta prueba cuando ya no sea necesaria:

```bash
rm -rf quality-results/dynamic-smoke-30
```

---

## 4. Dynamic Giant Gauntlet recomendado: 1.000 casos

La primera campaña grande recomendada utiliza:

```text
20 ejecuciones × 50 casos = 1.000 casos
```

La división en ejecuciones de 50 casos mejora la organización de los informes y limita el tamaño de cada bloque.

### 4.1 Lanzamiento desatendido

Copiar y pegar el bloque completo:

```bash
cd ~/MagicAI
source .venv/bin/activate
export PYTHONPATH=.

CAMPAIGN="dynamic-giant-1000-$(date +%Y%m%d-%H%M%S)"
BASE_SEED=20260714
RUNS=20
CASES=50
WORKERS=4
REPO="$(pwd)"
ROOT="$REPO/quality-results/$CAMPAIGN"
OUTPUT="$ROOT/results"
LOG="$ROOT/campaign.log"
PIDFILE="$ROOT/campaign.pid"

mkdir -p "$OUTPUT"

{
  echo "Campaign: $CAMPAIGN"
  echo "Purpose: evaluation"
  echo "Training allowed: false"
  echo "Automatic learning: false"
  echo "Automatic promotion: false"
  echo "Started: $(date --iso-8601=seconds)"
  echo "Repository: $REPO"
  echo "Branch: $(git branch --show-current)"
  echo "Commit: $(git rev-parse HEAD)"
  echo "Base seed: $BASE_SEED"
  echo "Runs: $RUNS"
  echo "Cases per run: $CASES"
  echo "Workers: $WORKERS"
  echo "Expected cases: $((RUNS * CASES))"
  echo
  echo "Git status:"
  git status --short
  echo
  python --version
  ollama --version 2>&1
} > "$ROOT/RUN_INFO.txt"

cat > "$ROOT/run_campaign.sh" <<EOF_RUNNER
#!/usr/bin/env bash
set +e
cd "$REPO"
source "$REPO/.venv/bin/activate"
export PYTHONPATH=.

python -u -m tests.quality.dynamic_campaign_test \\
  --base-seed $BASE_SEED \\
  --runs $RUNS \\
  --cases $CASES \\
  --workers $WORKERS \\
  --output-dir "$OUTPUT" \\
  --require-full-coverage

code=\$?
printf '%s\n' "\$code" > "$ROOT/EXIT_CODE"
printf 'Finished: %s\n' "\$(date --iso-8601=seconds)" >> "$ROOT/RUN_INFO.txt"
exit "\$code"
EOF_RUNNER

chmod +x "$ROOT/run_campaign.sh"
nohup "$ROOT/run_campaign.sh" > "$LOG" 2>&1 &
echo $! | tee "$PIDFILE"

printf '\nCampaña iniciada.\n'
printf 'Directorio: %s\n' "$ROOT"
printf 'Log:        %s\n' "$LOG"
printf 'PID:        %s\n' "$(cat "$PIDFILE")"
```

Se omiten intencionadamente:

- `--fail-fast`, porque interesa completar todos los casos aunque aparezcan fallos;
- `--fail-on-warn`, porque las advertencias también son material de diagnóstico.

Se mantiene:

- `--require-full-coverage`, para detectar si la campaña no recorrió todos los conceptos y plantillas seleccionados;
- `--workers 4`, punto inicial recomendado para campañas deterministas en un Ryzen 5 5600 con 32 GB de RAM.

Para campañas que fuercen el LLM local, comenzar con `--workers 2`, porque la VRAM y Ollama serán el límite. La campaña dinámica normal suele resolverse mediante rutas deterministas y aprovecha principalmente CPU.

### 4.2 Localizar la campaña más reciente

En otra terminal:

```bash
cd ~/MagicAI
LATEST=$(find quality-results -mindepth 1 -maxdepth 1 \
  -type d -name 'dynamic-giant-1000-*' | sort | tail -n 1)
printf '%s\n' "$LATEST"
```

Todos los comandos siguientes presuponen que la variable `LATEST` contiene ese directorio.

### 4.3 Ver el progreso

```bash
tail -f "$LATEST/campaign.log"
```

Salir de `tail` sin detener la campaña:

```text
Ctrl+C
```

### 4.4 Comprobar si sigue ejecutándose

```bash
PID=$(cat "$LATEST/campaign.pid")

if kill -0 "$PID" 2>/dev/null; then
  echo "La campaña sigue activa con PID $PID"
else
  echo "El proceso ya no está activo"
fi
```

### 4.5 Comprobar si ha terminado

```bash
if [[ -f "$LATEST/EXIT_CODE" ]]; then
  echo "Campaña terminada. Código de salida: $(cat "$LATEST/EXIT_CODE")"
else
  echo "La campaña todavía no ha registrado su finalización"
fi
```

Interpretación habitual:

```text
0 = campaña completada sin condición de fallo
1 = se encontraron FAIL o no se cumplió una puerta de calidad
2 = error de argumentos, fuentes ausentes u otro problema de preparación
```

Un código `1` es un resultado útil para una campaña de descubrimiento. Significa que hay material que revisar.

### 4.6 Ver el final del log

```bash
tail -n 100 "$LATEST/campaign.log"
```

### 4.7 Consultar el resumen agregado

```bash
python -m json.tool \
  "$LATEST/results/campaign_summary.json" | less
```

Abrir el informe HTML desde Windows, si el repositorio está en WSL:

```bash
explorer.exe "$(wslpath -w "$LATEST/results/campaign_summary.html")"
```

También se generan informes independientes por ejecución:

```text
results/
├── campaign_summary.json
├── campaign_summary.txt
├── campaign_summary.html
├── run_01_seed_.../
│   ├── manifest.json
│   ├── report.txt
│   ├── report.xml
│   ├── report.html
│   ├── run.log
│   ├── run_complete.json
│   └── failures/
├── run_02_seed_.../
└── ...
```

---

## 5. Reanudar una campaña dinámica

El runner guarda cada ejecución terminada mediante un `run_complete.json` escrito atómicamente. Para reanudar una campaña interrumpida, se utiliza exactamente el mismo directorio, semillas, número de casos, conceptos y snapshots de fuentes:

```bash
python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260714 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/mi-campana/results \
  --require-full-coverage \
  --resume
```

La reanudación:

- omite las ejecuciones que ya tengan un marcador completo y válido;
- vuelve a ejecutar un bloque incompleto desde el principio;
- permite cambiar el número de workers;
- rechaza mezclar cambios de código, modelo, semillas, casos, conceptos, Comprehensive Rules u Oracle;
- conserva un log independiente dentro de cada `run_*`.

El Dynamic Gauntlet reanuda por **bloques/semillas completos**. No reanuda a mitad de los 50 casos de una misma semilla. El Community Feedback Gauntlet sí tiene checkpoints por caso y `--retry-errors`.

Para reanudar el lanzamiento desatendido del apartado anterior:

```bash
LATEST=$(find quality-results -mindepth 1 -maxdepth 1 \
  -type d -name 'dynamic-giant-1000-*' | sort | tail -n 1)

python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260714 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir "$LATEST/results" \
  --require-full-coverage \
  --resume
```

---

## 6. Detener manualmente una campaña dinámica

Localizar la campaña y leer el PID:

```bash
cd ~/MagicAI
LATEST=$(find quality-results -mindepth 1 -maxdepth 1 \
  -type d -name 'dynamic-giant-1000-*' | sort | tail -n 1)
PID=$(cat "$LATEST/campaign.pid")
```

Solicitar una terminación normal:

```bash
kill "$PID"
```

Comprobar después:

```bash
kill -0 "$PID" 2>/dev/null \
  && echo "El proceso sigue activo" \
  || echo "El proceso se ha detenido"
```

No utilizar `kill -9` salvo que el proceso no responda a una terminación normal, porque impide cualquier limpieza pendiente del proceso.

---

## 7. Empaquetar la campaña para revisión

Una vez terminada, o si se ha interrumpido y se quiere conservar el diagnóstico:

```bash
cd ~/MagicAI
LATEST=$(find quality-results -mindepth 1 -maxdepth 1 \
  -type d -name 'dynamic-giant-1000-*' | sort | tail -n 1)

ARCHIVE="${LATEST}.tar.gz"
tar -C "$(dirname "$LATEST")" \
  -czf "$ARCHIVE" \
  "$(basename "$LATEST")"

sha256sum "$ARCHIVE" > "${ARCHIVE}.sha256"

printf 'Archivo:  %s\n' "$ARCHIVE"
printf 'Checksum: %s\n' "${ARCHIVE}.sha256"
```

Los dos archivos que deben compartirse son:

```text
quality-results/dynamic-giant-1000-...tar.gz
quality-results/dynamic-giant-1000-...tar.gz.sha256
```

El paquete contiene:

- información de rama, commit, semilla y estado de Git;
- log completo de ejecución;
- resumen agregado JSON, TXT y HTML;
- manifiestos reproducibles;
- informes de cada semilla;
- casos que produjeron fallos.

No es necesario incluir los archivos grandes originales de Scryfall si el informe ya identifica el estado de la ejecución. Si durante el análisis fuera necesario comprobar una versión concreta de Oracle, se solicitará por separado.

---

## 8. Campaña posterior de 5.000 casos

No se recomienda empezar directamente con 5.000 casos. Primero debe analizarse la campaña de 1.000, corregir causas estructurales y ejecutar las regresiones.

Después puede repetirse el bloque de lanzamiento modificando únicamente:

```bash
CAMPAIGN="dynamic-giant-5000-$(date +%Y%m%d-%H%M%S)"
BASE_SEED=2026071501
RUNS=50
CASES=100
```

El total será:

```text
50 ejecuciones × 100 casos = 5.000 casos
```

Mantener inicialmente `WORKERS=4`. Comparar casos por minuto y memoria antes de aumentarlo; más procesos no garantizan más rendimiento.

Para localizarla posteriormente:

```bash
LATEST=$(find quality-results -mindepth 1 -maxdepth 1 \
  -type d -name 'dynamic-giant-5000-*' | sort | tail -n 1)
```

El resto de comandos de monitorización y empaquetado son iguales.

---

## 9. Campañas limitadas a conceptos concretos

Listar conceptos:

```bash
python -m tests.quality.dynamic_campaign_test --list-concepts
```

Ejemplo centrado en varias familias reglamentarias:

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 2026071401 \
  --runs 10 \
  --cases 30 \
  --workers 4 \
  --concept mana_ability \
  --concept ward \
  --concept source_independence \
  --output-dir quality-results/dynamic-focused-300 \
  --require-full-coverage
```

Utilizar campañas focalizadas cuando un informe anterior muestre una concentración clara de fallos en una familia. La corrección debe seguir siendo genérica; restringir la campaña no autoriza a introducir condicionales por carta, pregunta o identificador de test.

---

## 10. Utilizar un archivo Oracle alternativo

El runner acepta:

```text
--oracle-file RUTA
```

Ejemplo:

```bash
python -m tests.quality.dynamic_campaign_test \
  --base-seed 2026071402 \
  --runs 5 \
  --cases 50 \
  --workers 4 \
  --oracle-file sources/scryfall/oracle-cards.json \
  --output-dir quality-results/dynamic-oracle-check-250 \
  --require-full-coverage
```

La ruta predeterminada ya es la fuente Oracle local del proyecto. La opción solo es necesaria para comparar snapshots o utilizar una ubicación distinta.

No mezclar resultados obtenidos con snapshots Oracle diferentes dentro del mismo directorio de campaña.

---

## 11. Community Feedback Gauntlet reanudable

Este runner ejecuta preguntas preparadas manualmente. No genera automáticamente los escenarios desde Oracle.

### 11.1 Crear una plantilla segura

```bash
python -m tests.quality.community_feedback_test \
  --create-template community_feedback/inbox/mi_caso.json
```

También puede utilizarse **Crear caso Gauntlet** desde la UI.

### 11.2 Ejecutar cientos o miles de casos preparados

```bash
python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --checkpoint-every 25
```

### 11.3 Reanudar después de una interrupción

```bash
python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --resume
```

### 11.4 Reintentar únicamente errores de ejecución

```bash
python -m tests.quality.community_feedback_test \
  --input community_feedback/inbox \
  --campaign-id judge-eval-001 \
  --resume \
  --retry-errors
```

### 11.5 Salida principal

```text
resultado_community_feedback/judge-eval-001/
├── campaign_manifest.json
├── campaign_progress.json
├── community_feedback_summary.json
├── community_feedback_summary.md
├── community_feedback_summary.html
├── findings_by_family.json
├── replay_commands.txt
├── completed/
├── execution_errors/
└── review_packets/
```

Los archivos prioritarios para revisión técnica son:

```text
campaign_manifest.json
findings_by_family.json
community_feedback_summary.html
review_packets/
```

### 11.6 Empaquetar resultados

```bash
cd ~/MagicAI
CAMPAIGN_ID="judge-eval-001"
SOURCE="resultado_community_feedback/$CAMPAIGN_ID"
ARCHIVE="quality-results/community-feedback-${CAMPAIGN_ID}.tar.gz"

mkdir -p quality-results
tar -czf "$ARCHIVE" "$SOURCE"
sha256sum "$ARCHIVE" > "${ARCHIVE}.sha256"

printf 'Archivo:  %s\n' "$ARCHIVE"
printf 'Checksum: %s\n' "${ARCHIVE}.sha256"
```

---

## 12. Validación después de modificar el Juez

Antes de comparar una campaña nueva con una anterior:

```bash
python -m compileall -q magicai tests
git diff --check
```

Ejecutar las pruebas de generación dinámica:

```bash
python -m tests.quality.dynamic_ability_premise_test
python -m tests.quality.dynamic_gauntlet_generator_test
python -m tests.quality.dynamic_campaign_planner_test
python -m tests.quality.dynamic_campaign_parallel_test
python -m tests.quality.dynamic_concept_contract_test
python -m tests.retrieval.rule_service_index_test
```

Ejecutar las pruebas del Community Feedback Gauntlet:

```bash
python -m tests.quality.community_feedback_loader_test
python -m tests.quality.community_feedback_execution_test
python -m tests.quality.community_feedback_reports_test
python -m tests.quality.community_feedback_diagnostics_test
python -m tests.quality.community_feedback_campaign_test
```

Ejecutar regresiones y pruebas de generalización:

```bash
python -m tests.quality.reddit_gauntlet_test
python -m tests.quality.generalization_probe_test
python -m tests.regression.regression_test
```

La corrección de una familia de fallos no se considera completa hasta que:

1. mejora los casos afectados;
2. funciona con cartas y redacciones distintas;
3. no rompe los Gauntlets anteriores;
4. no introduce condiciones por nombre de carta o ID de caso;
5. sigue recuperando Oracle, rulings y Comprehensive Rules como fuentes de autoridad.

---

## 13. Comparación recomendada entre campañas

Para comparar antes y después de un cambio, mantener constantes:

- `BASE_SEED`;
- número de ejecuciones;
- casos por ejecución;
- conceptos seleccionados;
- snapshot Oracle;
- Comprehensive Rules y rulings;
- modelo local y configuración;
- versión del código, identificada mediante commit.

Ejemplo conceptual:

```text
Campaña A
commit: abc1234
base seed: 20260714
runs: 20
cases: 50

Campaña B
commit: def5678
base seed: 20260714
runs: 20
cases: 50
```

Después puede ejecutarse otra campaña con una semilla diferente para verificar que la mejora no se limita al conjunto utilizado durante el diagnóstico.

---

## 14. Limpieza de artefactos locales

Los resultados de desarrollo se guardan preferentemente bajo:

```text
quality-results/
```

Ese directorio está ignorado por Git.

Comprobar el espacio utilizado:

```bash
du -sh quality-results
du -h --max-depth=1 quality-results | sort -h
```

Eliminar una campaña concreta:

```bash
rm -rf quality-results/NOMBRE_DE_LA_CAMPAÑA
```

Eliminar únicamente archivos comprimidos antiguos:

```bash
find quality-results -maxdepth 1 -type f \
  \( -name '*.tar.gz' -o -name '*.sha256' \) \
  -print
```

Revisar la lista antes de sustituir `-print` por `-delete`.

---

## 15. Reglas de seguridad del proceso de evaluación

No convertir automáticamente las respuestas generadas en:

```text
training.jsonl
fine_tuning_dataset.json
prompt_completion.jsonl
learned_examples.json
```

No utilizar un fallo para añadir soluciones como:

```python
if card_name == "Nombre de una carta concreta":
    return "respuesta preparada"
```

El flujo correcto es:

```text
campaña de evaluación
→ agrupación de fallos
→ revisión humana
→ verificación contra CR + Oracle + rulings
→ identificación de la causa general
→ cambio de código genérico
→ prueba focalizada
→ prueba de generalización
→ regresiones completas
```

Los informes pueden conservarse para comparar versiones. No son memoria factual del modelo ni archivos de aprendizaje.


Resumen, lanza este comando para 1000 casos:
```bash
cd ~/MagicAI
source .venv/bin/activate

CAMPAIGN="dynamic-giant-1000-20260714"
OUTPUT="resultado_${CAMPAIGN}"
LOG="logs/${CAMPAIGN}.log"
PIDFILE="logs/${CAMPAIGN}.pid"

mkdir -p "$OUTPUT" logs

{
  echo "Campaign: $CAMPAIGN"
  echo "Started: $(date --iso-8601=seconds)"
  echo "Branch: $(git branch --show-current)"
  echo "Commit: $(git rev-parse HEAD)"
  echo
  echo "Git status:"
  git status --short
  echo
  python --version
  ollama --version
} > "$OUTPUT/RUN_INFO.txt"

nohup env PYTHONPATH=. python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260714 \
  --runs 20 \
  --cases 50 \
  --output-dir "$OUTPUT" \
  --require-full-coverage \
  > "$LOG" 2>&1 &

echo $! | tee "$PIDFILE"

echo
echo "Campaña iniciada."
echo "Salida: $OUTPUT"
echo "Log: $LOG"
echo "PID: $(cat "$PIDFILE")"
```

Y estos comandos para:

Ver el progreso:
```bash
tail -f logs/dynamic-giant-1000-20260714.log
```

Ver si sigue activo:
```bash
PID=$(cat logs/dynamic-giant-1000-20260714.pid)

if kill -0 "$PID" 2>/dev/null; then
  echo "El Gauntlet sigue ejecutándose con PID $PID"
else
  echo "El proceso ha terminado"
fi
```

---

## 16. Revalidación exacta de Research C1.3

Research C1.3 se validó repitiendo exactamente las semillas de la campaña que descubrió el fallo de Ward:

```bash
python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260715 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/dynamic-giant-1000-C13 \
  --require-full-coverage
```

Resultado de referencia:

```text
Cases     : 1000
Failures  : 0
Warnings  : 0
Templates : 42/42
Origins   : {'deterministic_rule': 1000}
LLM calls : 0
Status    : PASS
```

El hecho de que `LLM calls` sea cero es relevante para esta campaña concreta: Ward y las demás familias cubiertas deben disponer de evidencia suficiente para utilizar sus rutas deterministas. No constituye una prohibición general de usar el LLM en preguntas abiertas.

### Qué audita C1.3 además del matcher

Antes de ejecutar el Juez:

- se reparsea la habilidad Oracle vinculada;
- se rechaza una fuente sacrificada, descartada o exiliada como coste;
- se comprueba la zona desde la que se activa;
- se verifica que la dependencia almacenada coincide con el parser actual.

Después de responder:

- Ward debe describirse como habilidad disparada;
- debe aparecer en la pila y poder recibir respuestas antes de resolverse;
- la falta de pago debe estar vinculada a contrarrestar el hechizo o habilidad;
- no puede afirmarse que se responde durante la resolución;
- la independencia de la fuente se valida según `independent`, `source_object`, `information` o `partial`.

### Repetir después de modificar estas capas

Debe utilizarse un directorio nuevo cuando cambie cualquiera de estos archivos, porque forman parte de la huella reproducible de campaña:

```text
magicai/oracle_abilities.py
magicai/retrieval/concept_evidence.py
magicai/context_enricher.py
magicai/validation/answer.py
magicai/validation/rule_renderer.py
tests/quality/dynamic/premise_validation.py
tests/quality/dynamic/semantic_validation.py
tests/quality/dynamic/concepts.py
```

No se debe usar `--resume` sobre una campaña creada con una huella anterior. El runner bloqueará esa mezcla de forma deliberada.

---

## 17. Revalidación de Research C1.4

C1.4 cambia el esquema de escenario y la huella de campaña. No se debe reanudar un directorio C1.3. Utiliza un directorio nuevo:

```bash
PYTHONPATH=. python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260715 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/dynamic-giant-1000-C14 \
  --require-full-coverage
```

Para reanudar esa misma campaña C1.4:

```bash
PYTHONPATH=. python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260715 \
  --runs 20 \
  --cases 50 \
  --workers 4 \
  --output-dir quality-results/dynamic-giant-1000-C14 \
  --require-full-coverage \
  --resume
```

### Qué debe comprobar el informe

```text
Cases     : 1000
Failures  : 0
Warnings  : 0
Templates : 42/42
LLM calls : 0
Status    : PASS
```

Además de esos contadores, revisa que los escenarios `source_independence` incluyan, cuando proceda:

- `source_may_be_removed_as_cost`;
- `source_may_be_target`;
- la habilidad Oracle completa, incluidas viñetas;
- una premisa que indique que la fuente no fue sacrificada para pagar;
- una premisa que excluya a la fuente de todos los objetivos.

### Corpus Oracle alternativo

El mismo archivo indicado con `--oracle-file` debe usarse tanto para seleccionar escenarios como para la recuperación del Juez:

```bash
PYTHONPATH=. python -u -m tests.quality.dynamic_campaign_test \
  --base-seed 20260715 \
  --runs 2 \
  --cases 42 \
  --workers 2 \
  --oracle-file /ruta/al/oracle-cards.json \
  --output-dir quality-results/c14-oracle-override \
  --require-full-coverage
```

La ruta y el SHA-256 del snapshot quedan registrados en `campaign_manifest.json`.

---

## 18. Research C1.5 — barrido exhaustivo de Oracle

El Dynamic Gauntlet aleatorio sirve para detectar regresiones y combinaciones de
semillas, pero no garantiza recorrer todas las habilidades candidatas. C1.5 añade
un barrido determinista que construye una situación vinculada por cada candidato
Oracle soportado.

Familias cubiertas:

```text
mana_ability
ward
undying_exile
source_independence
```

Con el snapshot Oracle utilizado durante C1.5, el plan completo contiene:

```text
Cartas soportadas              29.308
Habilidades de maná             1.794
Cartas con Ward                   163
Cartas con Undying                 22
Habilidades source-independence 5.958
Total                            7.937
```

Los recuentos pueden cambiar cuando se actualice Oracle o mejore el parser. El
manifest guarda el SHA-256 exacto del archivo utilizado.

### Auditoría estática previa

Genera el inventario completo y las anomalías del parser sin consultar al Juez:

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --static-only \
  --output-dir quality-results/oracle-exhaustive-C15-static
```

Archivos principales:

```text
campaign_manifest.json
static_summary.json
static_findings.jsonl.gz
scenarios.jsonl.gz
```

Un `static_findings` distinto de cero requiere revisión antes del barrido dinámico.

### Barrido exhaustivo recomendado

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir quality-results/oracle-exhaustive-C15
```

El modo predeterminado es **determinista únicamente**. Si una pregunta no puede
resolverse mediante las rutas deterministas, el runner bloquea el fallback a Ollama
y guarda el caso como fallo de cobertura. Esto evita que una ejecución de miles de
casos se quede esperando al modelo y separa claramente dos auditorías distintas:

```text
barrido exhaustivo → cobertura determinista
shadow LLM         → comportamiento del modelo
```

No se generan targets de entrenamiento ni se modifica el modelo.

### Reanudar

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 250 \
  --output-dir quality-results/oracle-exhaustive-C15 \
  --resume
```

Solo se omiten shards con `shard_complete.json`. La reanudación se rechaza si
cambian:

- Oracle o su SHA-256;
- código del parser, Juez, contratos o runner;
- lista u orden de escenarios;
- familias seleccionadas;
- modo de plantillas;
- tamaño de shard;
- permiso de fallback al LLM.

El número de workers sí puede modificarse al reanudar.

### Prueba corta antes del barrido completo

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --workers 4 \
  --shard-size 25 \
  --max-cases 100 \
  --output-dir quality-results/oracle-exhaustive-C15-smoke
```

`--max-cases` es solo una herramienta de desarrollo. No debe usarse para presentar
el barrido como exhaustivo.

### Ejecutar las tres plantillas por candidato

El barrido normal rota una de las tres plantillas por candidato. Para ejecutar las
tres variantes:

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --template-mode all \
  --workers 4 \
  --shard-size 250 \
  --output-dir quality-results/oracle-exhaustive-C15-all-templates
```

Esto triplica el número de casos y debe hacerse después de que el barrido de una
plantilla quede limpio.

### Restringir familias

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --family source_independence \
  --workers 4 \
  --output-dir quality-results/oracle-exhaustive-C15-source
```

`--family` puede repetirse.

### Permitir Ollama deliberadamente

No debe usarse para el primer barrido exhaustivo. Solo para una campaña separada y
con Ollama disponible:

```bash
PYTHONPATH=. python -u -m tests.quality.oracle_exhaustive_test \
  --allow-llm \
  --workers 2 \
  --output-dir quality-results/oracle-exhaustive-C15-llm
```

Para una auditoría del modelo será preferible el futuro modo `shadow-llm`, que
comparará la respuesta de Qwen con la autoridad determinista sin sustituirla.

### Formato compacto

Cada shard produce:

```text
shard_0001/
├── results.jsonl.gz
├── failures/
├── run.log
└── shard_complete.json
```

No se generan informes HTML/XML completos por shard. El formato compacto conserva:

- pregunta y respuesta;
- escenario y habilidad Oracle exacta;
- estado, fallos y avisos;
- origen del Juez;
- si se llamó al LLM;
- reglas y tiempos registrados.

### Empaquetar para auditoría

```bash
cd ~/MagicAI

tar -czf MagicAI-oracle-exhaustive-C15.tar.gz \
  quality-results/oracle-exhaustive-C15

sha256sum MagicAI-oracle-exhaustive-C15.tar.gz \
  > MagicAI-oracle-exhaustive-C15.tar.gz.sha256
```

Facilita ambos archivos. No elimines los `PASS`: también se revisan para buscar
falsos positivos compartidos por generador y validador.
