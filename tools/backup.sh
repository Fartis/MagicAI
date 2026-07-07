#!/usr/bin/env bash

set -e

###############################################################################
# CONFIGURACIÓN
###############################################################################

PROJECT_NAME="MagicAI"
BACKUP_ROOT="/home/fartis/backup"

DATE=$(date +%Y-%m-%d)
VERSION="v0.1.0-alpha"

DEST="$BACKUP_ROOT/$DATE"

###############################################################################
# COMPROBACIONES
###############################################################################

if [ ! -f "pyproject.toml" ]; then
    echo "ERROR: Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

mkdir -p "$DEST"

echo
echo "=============================================="
echo " MagicAI Backup"
echo "=============================================="
echo

echo "Destino:"
echo "$DEST"
echo

echo "Generando información del proyecto..."

{
    echo "MagicAI"
    echo
    echo "Fecha: $(date)"
    echo
    echo "Git:"
    git status 2>/dev/null || true
    echo
    echo "Python:"
    python --version
    echo
    echo "Ollama:"
    docker exec ollama ollama --version 2>/dev/null || true
} > "$DEST/INFO.txt"

###############################################################################
# ZIP DEL CÓDIGO
###############################################################################

SOURCE_ZIP="$DEST/${PROJECT_NAME}-${VERSION}-source.zip"

echo "Creando backup del código..."

zip -rq "$SOURCE_ZIP" . \
    -x ".git/*" \
    -x ".venv/*" \
    -x "**/__pycache__/*" \
    -x "*.pyc" \
    -x ".pytest_cache/*" \
    -x ".mypy_cache/*" \
    -x ".ruff_cache/*" \
    -x ".idea/*" \
    -x ".vscode/*" \
    -x "magicai.egg-info/*" \
    -x "Resultado.txt" \
    -x "database/magic.db" \
    -x "sources/scryfall/*" \
    -x "sources/commander/*" \
    -x "sources/strategy/*"

###############################################################################
# ZIP COMPLETO
###############################################################################

FULL_ZIP="$DEST/${PROJECT_NAME}-${VERSION}-full.zip"

echo "Creando snapshot completo..."

zip -rq "$FULL_ZIP" . \
    -x ".git/*" \
    -x ".venv/*" \
    -x "**/__pycache__/*" \
    -x "*.pyc" \
    -x ".pytest_cache/*" \
    -x ".mypy_cache/*" \
    -x ".ruff_cache/*" \
    -x ".idea/*" \
    -x ".vscode/*" \
    -x "magicai.egg-info/*" \
    -x "Resultado.txt"

###############################################################################
# RESUMEN
###############################################################################

echo
echo "=============================================="
echo " Backup completado"
echo "=============================================="
echo

echo "Código:"
ls -lh "$SOURCE_ZIP"

echo

echo "Snapshot:"
ls -lh "$FULL_ZIP"

echo

echo "Archivos creados en:"
echo "$DEST"

echo