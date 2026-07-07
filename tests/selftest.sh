#!/bin/bash

OUTPUT="Resultado.txt"

echo "==============================================" > "$OUTPUT"
echo "        MagicAI Self Test Report" >> "$OUTPUT"
echo "==============================================" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "Fecha: $(date)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

########################################################
echo "========== PYTHON ==========" >> "$OUTPUT"
echo "" >> "$OUTPUT"

which python >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

python --version >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

echo "========== IMPORT MAGICAI ==========" >> "$OUTPUT"

python -c "import magicai; print('OK')" >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== TREE ==========" >> "$OUTPUT"

tree -L 3 >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== OLLAMA VERSION ==========" >> "$OUTPUT"

curl http://127.0.0.1:11434/api/version >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== OLLAMA MODELS ==========" >> "$OUTPUT"

docker exec -it ollama ollama list >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== SCRYFALL ==========" >> "$OUTPUT"

python scripts/explore_scryfall.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== CARD SEARCH ==========" >> "$OUTPUT"

python scripts/search_card.py "Young Wolf" >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

python scripts/search_card.py "Prossh, Skyraider of Kher" >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== RULE SEARCH ==========" >> "$OUTPUT"

python scripts/search_rule.py "Undying" >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== EXTRACTORS ==========" >> "$OUTPUT"

printf "Young Wolf\n\n" | python tests/test_extractors.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

printf "¿Young Wolf tiene Undying?\n\n" | python tests/test_extractors.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== CONTEXT BUILDER ==========" >> "$OUTPUT"

printf "¿Young Wolf tiene Undying?\n\n" | python tests/test_context.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== ENRICHER ==========" >> "$OUTPUT"

printf "¿Young Wolf tiene Undying?\n\n" | python tests/test_enricher.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== QWEN ==========" >> "$OUTPUT"

printf "¿Qué hace Young Wolf?\n\n" | python tests/test_qwen.py >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

########################################################
echo "========== GIT ==========" >> "$OUTPUT"

git status >> "$OUTPUT" 2>&1

echo "" >> "$OUTPUT"

echo "==============================================" >> "$OUTPUT"
echo " Fin del informe" >> "$OUTPUT"
echo "==============================================" >> "$OUTPUT"

echo
echo "Informe generado en:"
echo
echo "  $OUTPUT"
echo