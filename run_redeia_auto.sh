#!/bin/bash
set -e

CLIENT="REDEIA"
WORKING_DIR="working/${CLIENT}"
CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

echo "1/5 Ejecutando Minuto Cero (Inteligencia OSINT)..."
./.venv/bin/python -m assessment_engine.scripts.run_intelligence_harvesting ${CLIENT}

echo "2/5 Procesando las Torres Técnicas en serie (esto llevará unos minutos)..."
for t in T2 T4 T5 T6 T7 T8 T10; do
  echo ">>> Iniciando Torre $t..."
  ./.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline \
    --tower $t \
    --client ${CLIENT} \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}"
done

echo "3/5 Ejecutando Consolidación Global..."
./.venv/bin/python -m assessment_engine.scripts.run_global_pipeline ${CLIENT}

echo "4/5 Ejecutando Refinado Comercial y Account Action Plan..."
./.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline ${CLIENT}

echo "5/5 Generando Dashboard Web..."
./.venv/bin/python -m assessment_engine.scripts.render_web_presentation ${CLIENT}

echo "=== ✅ PROCESO END-TO-END COMPLETADO ==="
