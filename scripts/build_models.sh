#!/bin/bash

set -e

echo "Construyendo magicai-intent..."

ollama create magicai-intent \
-f models/intent/Modelfile

echo
echo "Modelo creado correctamente."