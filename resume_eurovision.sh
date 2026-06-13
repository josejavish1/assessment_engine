#!/bin/bash
CLIENT="Eurovision Services"
SLUG="eurovision_services"
CONTEXT="working/eurovision_demo_ultimate/contexto_eurovision_elite.docx"
RESPONSES="working/eurovision_demo_ultimate/preguntas_eurovision_con_notas_v2.txt"
TOWERS=("T3" "T4" "T5" "T6" "T7" "T8")

source .env
export GOOGLE_APPLICATION_CREDENTIALS=/home/jsanchhi/.secrets/sa-key.json
export PYTHONPATH=src

echo "========================================================"
echo " RESUMIENDO PIPELINE DE EUROVISION SERVICES DESDE FASE 2"
echo "========================================================"

for TOWER in "${TOWERS[@]}"; do
    echo ""
    echo "▶️ PROCESANDO TORRE $TOWER"
    echo "--------------------------------------------------------"
    ./.venv/bin/python src/application/run_tower_pipeline.py \
        --tower "$TOWER" \
        --client "$CLIENT" \
        --context-file "$CONTEXT" \
        --responses-file "$RESPONSES"
        
    if [ $? -ne 0 ]; then
        echo "❌ Fallo en la ejecución de la torre $TOWER. Deteniendo el pipeline."
        exit 1
    fi
done

echo "🌍 FASE 3: Ejecutando Consolidación Global..."
./.venv/bin/python -m src.application.run_global_pipeline "${SLUG}"

echo "💼 FASE 4: Ejecutando Refinado Comercial..."
./.venv/bin/python -m src.application.run_commercial_pipeline "${SLUG}"

echo "🖥️ FASE 5: Generando Dashboard Web..."
./.venv/bin/python -m src.adapters.render_web_presentation "${SLUG}"

echo ""
echo "✅ EJECUCIÓN DEL PIPELINE COMPLETADA PARA TODAS LAS TORRES Y ENTREGABLES GLOBALES."
