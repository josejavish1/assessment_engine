
#!/bin/bash
# Script para generar la demo multi-torre de Eurovision Services

CLIENT="Eurovision Demo V2"
CONTEXT="working/eurovision_demo/inputs/contexto_eurovision_v2.docx"
RESPONSES="working/eurovision_demo/inputs/preguntas_eurovision_v2.txt"
TOWERS=("T2" "T3" "T4" "T5" "T8")

mkdir -p working/eurovision_demo/output

for TOWER in "${TOWERS[@]}"; do
    echo "--- PROCESANDO TORRE $TOWER ---"
    source .env
    ./.venv/bin/python src/application/run_tower_pipeline.py \
        --tower "$TOWER" \
        --client "$CLIENT" \
        --context-file "$CONTEXT" \
        --responses-file "$RESPONSES"
done

echo "Demo generation complete."
