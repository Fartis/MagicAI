#!/bin/bash

set -e

BASE="$HOME/MagicAI/sources"

mkdir -p "$BASE/scryfall"
mkdir -p "$BASE/rules"
mkdir -p "$BASE/commander"
mkdir -p "$BASE/strategy"

download_bulk() {
    TYPE="$1"
    OUTPUT="$2"

    echo "==> Descargando $TYPE..."

    URL=$(curl -s https://api.scryfall.com/bulk-data \
        | jq -r ".data[] | select(.type==\"$TYPE\") | .download_uri")

    wget -q --show-progress -O "$OUTPUT" "$URL"

    echo "OK"
    echo
}

download_bulk "oracle_cards" \
"$BASE/scryfall/oracle-cards.json"

download_bulk "default_cards" \
"$BASE/scryfall/default-cards.json"

echo "Todo descargado correctamente."
