#!/usr/bin/env bash

set -euo pipefail

BASE="${MAGICAI_SOURCES_DIR:-$HOME/MagicAI/sources}"
SCRYFALL_DIR="$BASE/scryfall"

mkdir -p "$SCRYFALL_DIR"

download_bulk() {
    local type="$1"
    local output="$2"

    echo "==> Descargando $type..."

    local url
    url="$(
        curl --fail --silent --show-error https://api.scryfall.com/bulk-data \
            | jq -r ".data[] | select(.type==\"$type\") | .download_uri"
    )"

    if [[ -z "$url" || "$url" == "null" ]]; then
        echo "ERROR: Scryfall no devolvió una URL para $type."
        exit 1
    fi

    wget --quiet --show-progress --output-document="$output.part" "$url"
    mv "$output.part" "$output"

    echo "OK: $output"
    echo
}

# El Juez actual trabaja con objetos Oracle únicos. default_cards ocupa mucho
# más espacio y no tiene consumidores en el pipeline, así que no se descarga.
download_bulk "oracle_cards" "$SCRYFALL_DIR/oracle-cards.json"

echo "Fuentes Scryfall necesarias descargadas correctamente."
