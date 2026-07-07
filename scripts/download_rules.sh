#!/bin/bash

set -e

BASE="$HOME/MagicAI/sources/rules"

mkdir -p "$BASE"

echo "==> Buscando la última versión de las Comprehensive Rules..."

PAGE=$(curl -s https://magic.wizards.com/en/rules)

TXT_URL=$(echo "$PAGE" | grep -o 'https://media\.wizards\.com[^"]*MagicCompRules[^"]*\.txt' | head -n1)

if [ -z "$TXT_URL" ]; then
    echo "No se ha encontrado el enlace al TXT."
    exit 1
fi

echo "Encontrado:"
echo "$TXT_URL"
echo

echo "==> Descargando..."

wget -O "$BASE/MagicCompRules.txt" "$TXT_URL"

echo
echo "Comprehensive Rules descargadas correctamente."