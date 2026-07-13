#!/usr/bin/env bash

set -euo pipefail

PROJECT_NAME="MagicAI"
BACKUP_ROOT="${MAGICAI_BACKUP_ROOT:-$HOME/backup}"
DATE="$(date +%Y-%m-%d)"

if [[ ! -f "pyproject.toml" ]]; then
    echo "ERROR: Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

VERSION="v$(python - <<'PY'
import tomllib
from pathlib import Path
payload = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
print(payload['project']['version'])
PY
)-alpha"
DEST="$BACKUP_ROOT/$DATE"

mkdir -p "$DEST"

cat <<INFO

==============================================
 MagicAI Backup
==============================================

Destino:
$DEST
INFO

{
    echo "MagicAI"
    echo
    echo "Fecha: $(date --iso-8601=seconds 2>/dev/null || date)"
    echo "Versión: $VERSION"
    echo
    echo "Git:"
    git status 2>/dev/null || true
    echo
    echo "Python:"
    python --version
    echo
    echo "Ollama:"
    docker exec ollama ollama --version 2>/dev/null || ollama --version 2>/dev/null || true
} > "$DEST/INFO.txt"

COMMON_EXCLUDES=(
    ".git/*"
    ".venv/*"
    "venv/*"
    "**/__pycache__/*"
    "*.pyc"
    ".pytest_cache/*"
    ".mypy_cache/*"
    ".ruff_cache/*"
    ".idea/*"
    ".vscode/*"
    "*.egg-info/*"
    "build/*"
    "dist/*"
    "resultado_*.txt"
    "resultado_*.xml"
    "resultado_*.html"
    "resultado_*.json"
    "resultado_dynamic_gauntlet_failures/*"
    "resultado_dynamic_campaign/*"
    "quality-results/*"
    "test-results/*"
    "reports/*"
    "tests/regression/output/*"
    "resultado_open_judge/*"
    "audit_gauntlet_*_failures.txt"
    "sprint*.patch"
    "MagicAI-*.zip"
    "*.db"
    "*.sqlite*"
)

zip_project() {
    local output="$1"
    shift

    # `zip` actualiza archivos existentes, pero no elimina entradas que ya no
    # existen en el árbol. Crear primero un archivo temporal evita que un backup
    # reutilizado conserve módulos borrados o resultados antiguos.
    local temporary_output="${output%.zip}.tmp.zip"
    rm -f "$temporary_output" "$output"

    local args=(zip -rq "$temporary_output" .)

    for pattern in "${COMMON_EXCLUDES[@]}" "$@"; do
        args+=(-x "$pattern")
    done

    if ! "${args[@]}"; then
        rm -f "$temporary_output"
        return 1
    fi

    mv "$temporary_output" "$output"
}

SOURCE_ZIP="$DEST/${PROJECT_NAME}-${VERSION}-source.zip"
echo "Creando backup del código..."
zip_project "$SOURCE_ZIP" \
    "sources/scryfall/oracle-cards.json" \
    "sources/scryfall/default-cards.json" \
    "sources/scryfall/all-cards.json" \
    "sources/scryfall/unique-artwork.json" \
    "sources/scryfall/rulings.json"

FULL_ZIP="$DEST/${PROJECT_NAME}-${VERSION}-full.zip"
echo "Creando snapshot completo..."
zip_project "$FULL_ZIP"

cat <<INFO

==============================================
 Backup completado
==============================================

Código:
$(ls -lh "$SOURCE_ZIP")

Snapshot:
$(ls -lh "$FULL_ZIP")

Archivos creados en:
$DEST
INFO
